#include "stm32f446xx.h"
#include <stdint.h>

#define IN3_PORT GPIOA
#define IN3_PIN 8

#define IN4_PORT GPIOB
#define IN4_PIN 10

#define ENB_PORT GPIOB
#define ENB_PIN 4

#define USART2_BRR_1MBPS 30U

#define TIM6_PSC_1KHZ 59U
#define TIM6_ARR_1KHZ 999U

#define PWM_PSC 59U
#define PWM_ARR 999U

#define PKT_HDR0 0xAA
#define PKT_HDR1 0x55
#define PKT_LEN 9

#define TX_BUF_SZ 256
static volatile uint8_t tx_buf[TX_BUF_SZ];
static volatile uint16_t tx_w = 0;
static volatile uint16_t tx_r = 0;

static volatile uint16_t adc_dma[2];

static const float Kp = 0.03f;
static const int16_t DEAD10 = 100;
static const float U_MIN = 0.15f;
static const float U_MAX = 0.85f;

#define DEG10_MIN  200
#define DEG10_MAX  1650

static void PLL_config(void);
static void GPIO_all_config(void);
static void USART2_config(void);
static void TIM6_config_irq(void);
static void TIM3_pwm_config(void);
static void ADC1_dma_config(void);

static inline uint8_t crc_xor8(const uint8_t *p, uint8_t n);
static void usart2_tx_push(const uint8_t *p, uint32_t n);

static inline void motor_dir(int dir);
static inline void pwm_set_u01(float u01);

static inline void pin_out(GPIO_TypeDef *p, uint32_t pin) {
    p->MODER &= ~(3U << (pin*2));
    p->MODER |=  (1U << (pin*2));
    p->OTYPER &= ~(1U << pin);
}

static inline void pin_af(GPIO_TypeDef *p, uint32_t pin, uint32_t af) {
    p->MODER &= ~(3U << (pin*2));
    p->MODER |=  (2U << (pin*2));
    uint32_t idx = pin / 8;
    uint32_t sh  = (pin % 8) * 4;
    p->AFR[idx] &= ~(0xFU << sh);
    p->AFR[idx] |=  ((af & 0xFU) << sh);
}

static inline void pin_analog(GPIO_TypeDef *p, uint32_t pin) {
    p->MODER |= (3U << (pin*2));
    p->PUPDR &= ~(3U << (pin*2));
}

static inline void set_pin(GPIO_TypeDef *p, uint32_t pin, int v) {
    if (v) p->BSRR = (1U << pin);
    else   p->BSRR = (1U << (pin + 16));
}

static inline uint8_t crc_xor8(const uint8_t *p, uint8_t n) {
    uint8_t c = 0;
    for (uint8_t i = 0; i < n; i++) c ^= p[i];
    return c;
}

static inline void motor_dir(int dir) {
    if (dir > 0) {
        set_pin(IN3_PORT, IN3_PIN, 1);
        set_pin(IN4_PORT, IN4_PIN, 0);
    } else if (dir < 0) {
        set_pin(IN3_PORT, IN3_PIN, 0);
        set_pin(IN4_PORT, IN4_PIN, 1);
    } else {
        set_pin(IN3_PORT, IN3_PIN, 0);
        set_pin(IN4_PORT, IN4_PIN, 0);
    }
}

static inline void pwm_set_u01(float u01) {
    if (u01 < 0.0f) u01 = 0.0f;
    if (u01 > 1.0f) u01 = 1.0f;
    uint32_t ccr = (uint32_t)(u01 * (float)(PWM_ARR + 1U));
    if (ccr > PWM_ARR) ccr = PWM_ARR;
    TIM3->CCR1 = ccr;
}

static void usart2_tx_push(const uint8_t *p, uint32_t n) {
    for (uint32_t i = 0; i < n; i++) {
        uint16_t nw = (uint16_t)((tx_w + 1) & (TX_BUF_SZ - 1));
        if (nw == tx_r) break;
        tx_buf[tx_w] = p[i];
        tx_w = nw;
    }
    USART2->CR1 |= USART_CR1_TXEIE;
}

int main(void) {
    SCB->CPACR |= (3UL << (10 * 2)) | (3UL << (11 * 2));

    PLL_config();

    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN | RCC_AHB1ENR_GPIOBEN;
    RCC->APB1ENR |= RCC_APB1ENR_USART2EN | RCC_APB1ENR_TIM3EN | RCC_APB1ENR_TIM6EN;
    RCC->APB2ENR |= RCC_APB2ENR_ADC1EN;
    RCC->AHB1ENR |= RCC_AHB1ENR_DMA2EN;

    GPIO_all_config();
    USART2_config();
    TIM3_pwm_config();
    ADC1_dma_config();
    TIM6_config_irq();

    motor_dir(0);
    pwm_set_u01(0.0f);

    while (1) {
        __WFI();
    }
}

static void PLL_config(void) {
    FLASH->ACR = FLASH_ACR_ICEN | FLASH_ACR_DCEN | FLASH_ACR_PRFTEN | FLASH_ACR_LATENCY_3WS;

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
    RCC->CFGR |= (0U << RCC_CFGR_HPRE_Pos) |
                 (4U << RCC_CFGR_PPRE1_Pos) |
                 (0U << RCC_CFGR_PPRE2_Pos);

    RCC->CFGR |= RCC_CFGR_SW_PLL;
    while ((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_PLL) {}
}

static void GPIO_all_config(void) {
    pin_out(IN3_PORT, IN3_PIN);
    pin_out(IN4_PORT, IN4_PIN);

    pin_af(ENB_PORT, ENB_PIN, 2);

    pin_analog(GPIOA, 0);
    pin_analog(GPIOA, 1);

    pin_af(GPIOA, 2, 7);
    pin_af(GPIOA, 3, 7);
}

static void USART2_config(void) {
    USART2->CR1 = 0;
    USART2->CR2 = 0;
    USART2->CR3 = 0;

    USART2->BRR = USART2_BRR_1MBPS;

    USART2->CR1 = USART_CR1_TE | USART_CR1_RE | USART_CR1_RXNEIE;
    USART2->CR1 |= USART_CR1_UE;

    NVIC_SetPriority(USART2_IRQn, 2);
    NVIC_EnableIRQ(USART2_IRQn);
}

static void TIM6_config_irq(void) {
    TIM6->CR1 = 0;
    TIM6->PSC = TIM6_PSC_1KHZ;
    TIM6->ARR = TIM6_ARR_1KHZ;

    TIM6->DIER |= TIM_DIER_UIE;
    TIM6->EGR = TIM_EGR_UG;

    NVIC_SetPriority(TIM6_DAC_IRQn, 1);
    NVIC_EnableIRQ(TIM6_DAC_IRQn);

    TIM6->CR1 |= TIM_CR1_CEN;
}

static void TIM3_pwm_config(void) {
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

static void ADC1_dma_config(void) {
    ADC->CCR &= ~ADC_CCR_ADCPRE;
    ADC->CCR |=  (1U << ADC_CCR_ADCPRE_Pos);

    DMA2_Stream0->CR &= ~DMA_SxCR_EN;
    while (DMA2_Stream0->CR & DMA_SxCR_EN) {}

    DMA2_Stream0->PAR  = (uint32_t)&ADC1->DR;
    DMA2_Stream0->M0AR = (uint32_t)adc_dma;
    DMA2_Stream0->NDTR = 2;

    DMA2_Stream0->CR =
        (0U << DMA_SxCR_CHSEL_Pos) |
        DMA_SxCR_CIRC |
        DMA_SxCR_MINC |
        (1U << DMA_SxCR_PSIZE_Pos) |
        (1U << DMA_SxCR_MSIZE_Pos) |
        (2U << DMA_SxCR_PL_Pos);

    DMA2_Stream0->FCR = 0;

    ADC1->CR1 = ADC_CR1_SCAN;
    ADC1->CR2 = 0;

    ADC1->SMPR2 &= ~((7U << (3 * 0)) | (7U << (3 * 1)));
    ADC1->SMPR2 |=  ((4U << (3 * 0)) | (4U << (3 * 1)));

    ADC1->SQR1 &= ~ADC_SQR1_L;
    ADC1->SQR1 |= (1U << ADC_SQR1_L_Pos);

    ADC1->SQR3 = (0U << 0) | (1U << 5);

    ADC1->CR2 |= ADC_CR2_DMA | ADC_CR2_DDS | ADC_CR2_CONT;

    DMA2_Stream0->CR |= DMA_SxCR_EN;

    ADC1->CR2 |= ADC_CR2_ADON;
    ADC1->CR2 |= ADC_CR2_SWSTART;
}

void USART2_IRQHandler(void) {
    uint32_t sr = USART2->SR;

    if (sr & USART_SR_RXNE) {
        volatile uint8_t b = (uint8_t)USART2->DR;
        (void)b;
    }

    if ((sr & USART_SR_TXE) && (USART2->CR1 & USART_CR1_TXEIE)) {
        if (tx_r == tx_w) {
            USART2->CR1 &= ~USART_CR1_TXEIE;
        } else {
            USART2->DR = tx_buf[tx_r];
            tx_r = (uint16_t)((tx_r + 1) & (TX_BUF_SZ - 1));
        }
    }
}

void TIM6_DAC_IRQHandler(void) {
    if (TIM6->SR & TIM_SR_UIF) {
        TIM6->SR &= ~TIM_SR_UIF;

        uint16_t a_meas = adc_dma[0];
        uint16_t a_ref  = adc_dma[1];

        int16_t meas10 = (int16_t)((a_meas * 1800UL) / 4095UL);
        int16_t ref10  = (int16_t)((a_ref  * 1800UL) / 4095UL);

        int16_t err10 = (int16_t)(ref10 - meas10);

        float u = Kp * (float)err10;
        if (u > 1.0f)  u = 1.0f;
        if (u < -1.0f) u = -1.0f;

        if (err10 > -DEAD10 && err10 < DEAD10) u = 0.0f;

        if (meas10 <= DEG10_MIN + 5 && u < 0.0f) u = 0.0f;
        if (meas10 >= DEG10_MAX - 5 && u > 0.0f) u = 0.0f;

        int dir = 0;
        float pwm = 0.0f;

        if (u > 0.0f) {
            dir = +1;
            pwm = u;
        } else if (u < 0.0f) {
            dir = -1;
            pwm = -u;
        } else {
            dir = 0;
            pwm = 0.0f;
        }

        if (pwm > 0.0f && pwm < U_MIN) pwm = U_MIN;
        if (pwm > U_MAX) pwm = U_MAX;

        if (dir == 0) {
            motor_dir(0);
            pwm_set_u01(0.0f);
        } else {
            motor_dir(dir);
            pwm_set_u01(pwm);
        }

        uint8_t pkt[PKT_LEN];
        pkt[0] = PKT_HDR0;
        pkt[1] = PKT_HDR1;

        pkt[2] = (uint8_t)(meas10 & 0xFF);
        pkt[3] = (uint8_t)((meas10 >> 8) & 0xFF);

        pkt[4] = (uint8_t)(ref10 & 0xFF);
        pkt[5] = (uint8_t)((ref10 >> 8) & 0xFF);

        pkt[6] = (uint8_t)(err10 & 0xFF);
        pkt[7] = (uint8_t)((err10 >> 8) & 0xFF);

        pkt[8] = crc_xor8(pkt, 8);

        usart2_tx_push(pkt, PKT_LEN);
    }
}
