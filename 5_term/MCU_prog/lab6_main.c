#include <stdint.h>
#include "stm32f446xx.h"

#define PWM_PSC             59U
#define PWM_ARR             999U

#define CTRL_HZ             100UL
#define TELE_HZ             50UL

#define RPM_MAX             530.0f

#define DT_CTRL        (1.0f / (float)CTRL_HZ)

#define KNOB_TURNS_TO_MAXRPM  4.0f

static const float KP = 5.0f;
static const float KI = 0.5f;
static const float KFF = 1.0f / RPM_MAX;

volatile float g_rpm_ref  = 0.0f;
volatile float g_rpm_meas = 0.0f;
volatile float g_duty     = 0.0f;
volatile float g_i        = 0.0f;


volatile uint8_t tx_buf[32];
volatile uint8_t tx_len  = 0;
volatile uint8_t tx_pos  = 0;
volatile uint8_t tx_busy = 0;

void PLL_config(void);
void GPIO_motor_config(void);
void USART2_config_tx_only(void);

void TIM3_config_pwm(void);
void TIM4_config_encoder_motor(void);
void TIM2_config_encoder_knob(void);
void TIM6_config_control(void);
void TIM7_config_telemetry(void);

static inline void motor_set_dir(int8_t dir);
static inline void motor_set_pwm_u16(uint32_t ccr);
static inline uint8_t crc_xor8(const uint8_t *p, uint8_t n);
static inline void uart_send_packet(const uint8_t *data, uint8_t len);

static inline int16_t sat_i16(int32_t v)
{
    if (v > 32767) return 32767;
    if (v < -32768) return -32768;
    return (int16_t)v;
}

int main(void)
{
    SCB->CPACR |= (3UL << (10 * 2)) | (3UL << (11 * 2));

    PLL_config();

    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN
                 |  RCC_AHB1ENR_GPIOBEN
                 |  RCC_AHB1ENR_GPIOCEN
                 |  RCC_AHB1ENR_GPIODEN;

    GPIO_motor_config();

    TIM3_config_pwm();
    TIM4_config_encoder_motor();
    TIM2_config_encoder_knob();

    USART2_config_tx_only();
    TIM6_config_control();
    TIM7_config_telemetry();

    for (;;)
        __WFI();
}

void PLL_config(void)
{
    FLASH->ACR = FLASH_ACR_ICEN | FLASH_ACR_DCEN | FLASH_ACR_PRFTEN | FLASH_ACR_LATENCY_2WS;

    RCC->CR |= RCC_CR_HSEON;
    while (!(RCC->CR & RCC_CR_HSERDY)) {}

    RCC->PLLCFGR =
        RCC_PLLCFGR_PLLSRC_HSE |
        (8U   << RCC_PLLCFGR_PLLM_Pos) |
        (240U << RCC_PLLCFGR_PLLN_Pos) |
        (1U   << RCC_PLLCFGR_PLLP_Pos);

    RCC->CR |= RCC_CR_PLLON;
    while (!(RCC->CR & RCC_CR_PLLRDY)) {}

    RCC->CFGR &= ~(RCC_CFGR_HPRE | RCC_CFGR_PPRE1 | RCC_CFGR_PPRE2 | RCC_CFGR_SW);
    RCC->CFGR |= (0U << RCC_CFGR_HPRE_Pos)
              |  (4U << RCC_CFGR_PPRE1_Pos)
              |  (0U << RCC_CFGR_PPRE2_Pos);

    RCC->CFGR |= RCC_CFGR_SW_PLL;
    while ((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_PLL) {}
}

void GPIO_motor_config(void)
{
    GPIOA->MODER &= ~(3U << GPIO_MODER_MODE8_Pos);
    GPIOA->MODER |=  (1U << GPIO_MODER_MODE8_Pos);
    GPIOA->OTYPER &= ~(1U << GPIO_OTYPER_OT8_Pos);

    GPIOB->MODER &= ~(3U << GPIO_MODER_MODE10_Pos);
    GPIOB->MODER |=  (1U << GPIO_MODER_MODE10_Pos);
    GPIOB->OTYPER &= ~(1U << GPIO_OTYPER_OT10_Pos);

    motor_set_dir(0);
}

static inline void motor_set_dir(int8_t dir)
{
    if (dir > 0) {
        GPIOA->BSRR = (1U << GPIO_BSRR_BS8_Pos);
        GPIOB->BSRR = (1U << GPIO_BSRR_BR10_Pos);
    } else if (dir < 0) {
        GPIOA->BSRR = (1U << GPIO_BSRR_BR8_Pos);
        GPIOB->BSRR = (1U << GPIO_BSRR_BS10_Pos);
    } else {
        GPIOA->BSRR = (1U << GPIO_BSRR_BR8_Pos);
        GPIOB->BSRR = (1U << GPIO_BSRR_BR10_Pos);
    }
}

static inline void motor_set_pwm_u16(uint32_t ccr)
{
    if (ccr > PWM_ARR) ccr = PWM_ARR;
    TIM3->CCR1 = ccr;
}

void TIM3_config_pwm(void)
{
    RCC->APB1ENR |= RCC_APB1ENR_TIM3EN;

    GPIOB->MODER &= ~(3U << GPIO_MODER_MODE4_Pos);
    GPIOB->MODER |=  (2U << GPIO_MODER_MODE4_Pos);
    GPIOB->AFR[0] &= ~(0xFU << (4 * 4));
    GPIOB->AFR[0] |=  (2U   << (4 * 4));

    TIM3->CR1 = 0;
    TIM3->PSC = PWM_PSC;
    TIM3->ARR = PWM_ARR;
    TIM3->CCR1 = 0;

    TIM3->CCMR1 &= ~TIM_CCMR1_OC1M;
    TIM3->CCMR1 |= (6U << TIM_CCMR1_OC1M_Pos);
    TIM3->CCMR1 |= TIM_CCMR1_OC1PE;

    TIM3->CCER |= TIM_CCER_CC1E;
    TIM3->CR1  |= TIM_CR1_ARPE;
    TIM3->EGR   = TIM_EGR_UG;
    TIM3->CR1  |= TIM_CR1_CEN;
}

void TIM4_config_encoder_motor(void)
{
    RCC->APB1ENR |= RCC_APB1ENR_TIM4EN;

    GPIOB->MODER &= ~((3U << GPIO_MODER_MODE6_Pos) | (3U << GPIO_MODER_MODE7_Pos));
    GPIOB->MODER |=  ((2U << GPIO_MODER_MODE6_Pos) | (2U << GPIO_MODER_MODE7_Pos));
    GPIOB->PUPDR &= ~((3U << GPIO_PUPDR_PUPD6_Pos) | (3U << GPIO_PUPDR_PUPD7_Pos));
    GPIOB->PUPDR |=  ((1U << GPIO_PUPDR_PUPD6_Pos) | (1U << GPIO_PUPDR_PUPD7_Pos));
    GPIOB->AFR[0] &= ~((0xFU << (6 * 4)) | (0xFU << (7 * 4)));
    GPIOB->AFR[0] |=  ((2U   << (6 * 4)) | (2U   << (7 * 4)));

    TIM4->CR1 = 0;
    TIM4->ARR = 0xFFFF;
    TIM4->CNT = 0;

    TIM4->CCMR1 = 0;
    TIM4->CCMR1 |= (1U << TIM_CCMR1_CC1S_Pos) | (1U << TIM_CCMR1_CC2S_Pos);
    TIM4->CCMR1 |= (10U << TIM_CCMR1_IC1F_Pos) | (10U << TIM_CCMR1_IC2F_Pos);

    TIM4->SMCR = 0;
    TIM4->SMCR |= (3U << TIM_SMCR_SMS_Pos);

    TIM4->CCER = 0;
    TIM4->CR1 |= TIM_CR1_CEN;
}

void TIM2_config_encoder_knob(void)
{
    RCC->APB1ENR |= RCC_APB1ENR_TIM2EN;

    GPIOA->MODER &= ~((3U << GPIO_MODER_MODE0_Pos) | (3U << GPIO_MODER_MODE1_Pos));
    GPIOA->MODER |=  ((2U << GPIO_MODER_MODE0_Pos) | (2U << GPIO_MODER_MODE1_Pos));
    GPIOA->PUPDR &= ~((3U << GPIO_PUPDR_PUPD0_Pos) | (3U << GPIO_PUPDR_PUPD1_Pos));
    GPIOA->PUPDR |=  ((1U << GPIO_PUPDR_PUPD0_Pos) | (1U << GPIO_PUPDR_PUPD1_Pos));

    GPIOA->AFR[0] &= ~((0xFU << (0 * 4)) | (0xFU << (1 * 4)));
    GPIOA->AFR[0] |=  ((1U   << (0 * 4)) | (1U   << (1 * 4)));

    TIM2->CR1 = 0;
    TIM2->ARR = 0xFFFF;
    TIM2->CNT = 0x8000;

    TIM2->CCMR1 = 0;
    TIM2->CCMR1 |= (1U << TIM_CCMR1_CC1S_Pos) | (1U << TIM_CCMR1_CC2S_Pos);
    TIM2->CCMR1 |= (10U << TIM_CCMR1_IC1F_Pos) | (10U << TIM_CCMR1_IC2F_Pos);

    TIM2->SMCR = 0;
    TIM2->SMCR |= (3U << TIM_SMCR_SMS_Pos);

    TIM2->CCER = 0;
    TIM2->CR1 |= TIM_CR1_CEN;
}

void USART2_config_tx_only(void)
{
    RCC->APB1ENR |= RCC_APB1ENR_USART2EN;

    GPIOA->MODER &= ~(3U << GPIO_MODER_MODE2_Pos);
    GPIOA->MODER |=  (2U << GPIO_MODER_MODE2_Pos);
    GPIOA->AFR[0] &= ~(0xFU << (4 * 2));
    GPIOA->AFR[0] |=  (7U   << (4 * 2));

    USART2->BRR = 260U;
    USART2->CR1 = USART_CR1_TE | USART_CR1_UE;

    NVIC_SetPriority(USART2_IRQn, 3);
    NVIC_EnableIRQ(USART2_IRQn);
}

void USART2_IRQHandler(void)
{
    if (USART2->SR & USART_SR_TXE) {
        if (tx_busy && tx_pos < tx_len) {
            USART2->DR = tx_buf[tx_pos++];
            if (tx_pos >= tx_len) {
                tx_busy = 0;
                USART2->CR1 &= ~USART_CR1_TXEIE;
            }
        } else {
            tx_busy = 0;
            USART2->CR1 &= ~USART_CR1_TXEIE;
        }
    }
}

void TIM6_config_control(void)
{
    RCC->APB1ENR |= RCC_APB1ENR_TIM6EN;

    TIM6->PSC = 59999U;
    TIM6->ARR = (1000U / CTRL_HZ) - 1U;

    TIM6->DIER |= TIM_DIER_UIE;

    NVIC_SetPriority(TIM6_DAC_IRQn, 1);
    NVIC_EnableIRQ(TIM6_DAC_IRQn);

    TIM6->EGR = TIM_EGR_UG;
    TIM6->CR1 |= TIM_CR1_CEN;
}

void TIM6_DAC_IRQHandler(void)
{
    if (!(TIM6->SR & TIM_SR_UIF)) return;
    TIM6->SR &= ~TIM_SR_UIF;

    static uint16_t last_knob = 0x8000;
    uint16_t now_knob = (uint16_t)TIM2->CNT;
    int16_t d_knob = (int16_t)(now_knob - last_knob);
    last_knob = now_knob;

    float turns_knob = (float)d_knob / RPM_MAX;
    float rpm_per_turn = RPM_MAX / KNOB_TURNS_TO_MAXRPM;
    g_rpm_ref += turns_knob * rpm_per_turn;

    if (g_rpm_ref >  RPM_MAX) g_rpm_ref =  RPM_MAX;
    if (g_rpm_ref < -RPM_MAX) g_rpm_ref = -RPM_MAX;

    static uint16_t last_motor = 0;
    uint16_t now_motor = (uint16_t)TIM4->CNT;
    int16_t d_motor = (int16_t)(now_motor - last_motor);
    last_motor = now_motor;

    float cps = (float)d_motor * (float)CTRL_HZ;
    g_rpm_meas = (cps / RPM_MAX) * 60.0f;

    int8_t dir = (g_rpm_ref > 1.0f) ? +1 : (g_rpm_ref < -1.0f ? -1 : 0);
    motor_set_dir(dir);

    if (dir == 0) {
        motor_set_pwm_u16(0);
        g_i = 0.0f;
        g_duty = 0.0f;
        return;
    }

    float rpm_ref_abs  = (g_rpm_ref > 0.0f) ? g_rpm_ref : -g_rpm_ref;
    float rpm_meas_abs = (g_rpm_meas > 0.0f) ? g_rpm_meas : -g_rpm_meas;

    float e = (rpm_ref_abs - rpm_meas_abs) / 100;

    float duty_ff = KFF * rpm_ref_abs;

    float duty_unsat = duty_ff + KP * e + KI * g_i;

    float duty = duty_unsat;
    if (duty > 1.0f) duty = 1.0f;
    if (duty < 0.0f) duty = 0.0f;

    if (duty == duty_unsat) {
        g_i += e * DT_CTRL;
    }

    g_duty = duty;

    uint32_t ccr = (uint32_t)(duty * (float)(PWM_ARR + 1U));
    if (ccr > PWM_ARR) ccr = PWM_ARR;
    motor_set_pwm_u16(ccr);
}

void TIM7_config_telemetry(void)
{
    RCC->APB1ENR |= RCC_APB1ENR_TIM7EN;

    TIM7->PSC = 59999U;
    TIM7->ARR = (1000U / TELE_HZ) - 1U;

    TIM7->DIER |= TIM_DIER_UIE;

    NVIC_SetPriority(TIM7_IRQn, 4);
    NVIC_EnableIRQ(TIM7_IRQn);

    TIM7->EGR = TIM_EGR_UG;
    TIM7->CR1 |= TIM_CR1_CEN;
}

void TIM7_IRQHandler(void)
{
    if (!(TIM7->SR & TIM_SR_UIF)) return;
    TIM7->SR &= ~TIM_SR_UIF;

    int16_t meas10 = sat_i16((int32_t)(g_rpm_meas * 10.0f));
    int16_t ref10  = sat_i16((int32_t)(g_rpm_ref  * 10.0f));

    uint8_t p[7];
    p[0] = 0xAA;
    p[1] = 0x55;

    p[2] = (uint8_t)(meas10 & 0xFF);
    p[3] = (uint8_t)((meas10 >> 8) & 0xFF);

    p[4] = (uint8_t)(ref10 & 0xFF);
    p[5] = (uint8_t)((ref10 >> 8) & 0xFF);

    p[6] = crc_xor8(p, 6);

    uart_send_packet(p, 7);
}

static inline uint8_t crc_xor8(const uint8_t *p, uint8_t n)
{
    uint8_t c = 0;
    for (uint8_t i = 0; i < n; i++) c ^= p[i];
    return c;
}

static inline void uart_send_packet(const uint8_t *data, uint8_t len)
{
    if (tx_busy) return;
    for (uint8_t i = 0; i < len; i++) tx_buf[i] = data[i];
    tx_len = len;
    tx_pos = 0;
    tx_busy = 1;
    USART2->CR1 |= USART_CR1_TXEIE;
}
