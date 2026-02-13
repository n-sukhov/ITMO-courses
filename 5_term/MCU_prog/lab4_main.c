#include "stm32f446xx.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define SIN_AMPLITUDE 2.0
#define SIN_FREQ 20 //Hz
#define SAMPLES 400
#define VREF 3.3
#define PI 3.1415926f
#define DAC_RES 4095U

volatile uint16_t sin_table[SAMPLES];
volatile uint16_t sin_idx = 0;
volatile uint16_t adc_last = 0;

void PLL_config(void);
void USART2_config(void);
void DAC_config(void);
void ADC_config(void);
void TIM6_config(double freq_upd);
void TIM7_config(double uart_boundrate);


static inline void USART2_send_u8(uint8_t b) {
    while (!(USART2->SR & USART_SR_TXE)) {}
    USART2->DR = b;
}

static inline void USART2_send_u16_le(uint16_t x) {
    USART2_send_u8((uint8_t)(x & 0xFF));
    USART2_send_u8((uint8_t)(x >> 8));
}

static void sin_table_init(void) {
    for (uint16_t i = 0; i < SAMPLES; i++) {
        float a = 2.0f * PI * (float)i / (float)SAMPLES;

        float v = (VREF * 0.5f) + (SIN_AMPLITUDE * 0.5f) * sinf(a);

        if (v < 0.0f) v = 0.0f;
        if (v > VREF) v = VREF;

        float code = (v / VREF) * (float)DAC_RES;
        if (code < 0.0f) code = 0.0f;
        if (code > (float)DAC_RES) code = (float)DAC_RES;

        sin_table[i] = (uint16_t)(code + 0.5f);
    }
}

int main(void) {
    SCB->CPACR |= (3UL << 10 * 2) | (3UL << 11 * 2);
    PLL_config();
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOCEN;
    USART2_config();
    DAC_config();
    ADC_config();
    sin_table_init();

    TIM6_config(SIN_FREQ * SAMPLES);
    TIM7_config(1000);

    while (1) {
        __WFI(); 
    }

}

void PLL_config(void) {
    FLASH->ACR = FLASH_ACR_ICEN | FLASH_ACR_DCEN | FLASH_ACR_PRFTEN | FLASH_ACR_LATENCY_2WS;

    RCC->CR |= RCC_CR_HSEON;
    while (!(RCC->CR & RCC_CR_HSERDY)) {}

    // PLL: HSE=8MHz, M=8 => 1MHz, N=240 => 240MHz, P=4 => 60MHz
    RCC->PLLCFGR =
        RCC_PLLCFGR_PLLSRC_HSE |
        (8U   << RCC_PLLCFGR_PLLM_Pos) |
        (240U << RCC_PLLCFGR_PLLN_Pos) |
        (1U   << RCC_PLLCFGR_PLLP_Pos);

    RCC->CR |= RCC_CR_PLLON;
    while (!(RCC->CR & RCC_CR_PLLRDY)) {}

    // AHB=/1, APB1=/2, APB2=/1
    RCC->CFGR &= ~(RCC_CFGR_HPRE | RCC_CFGR_PPRE1 | RCC_CFGR_PPRE2 | RCC_CFGR_SW);
    RCC->CFGR |= (0U << RCC_CFGR_HPRE_Pos) | (4U << RCC_CFGR_PPRE1_Pos) | (0U << RCC_CFGR_PPRE2_Pos);

    // SYSCLK -> PLL
    RCC->CFGR |= RCC_CFGR_SW_PLL;
    while ((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_PLL) {}
}

void USART2_config(void) {
    RCC->APB1ENR |= RCC_APB1ENR_USART2EN;
    
    GPIOA->MODER &= ~((3U << GPIO_MODER_MODER2_Pos) | (3U << GPIO_MODER_MODER3_Pos));
    GPIOA->MODER |=  ((2U << GPIO_MODER_MODER2_Pos) | (2U << GPIO_MODER_MODER3_Pos));
    GPIOA->AFR[0] &= ~((0xF << (4*2)) | (0xF << (4*3)));
    GPIOA->AFR[0] |=  ((7 << (4*2)) | (7 << (4*3))); 

    USART2->BRR = 30U;
    USART2->CR1 = USART_CR1_TE | USART_CR1_UE;
}

void DAC_config(void) {
    RCC->APB1ENR |= RCC_APB1ENR_DACEN;
    GPIOA->MODER |= (3 << GPIO_MODER_MODER4_Pos); // аналоговый режим
    DAC->CR = DAC_CR_EN1;
}

void ADC_config(void) {
    RCC->APB2ENR |= RCC_APB2ENR_ADC1EN;
    GPIOC->MODER |= (3 << GPIO_MODER_MODER2_Pos); // аналоговый режим

    ADC1->SQR1 = 0;        
    ADC1->SQR3 = 12;       
    ADC1->SMPR1 &= ~(7U << (3 *  (12 - 10)));              
    ADC1->SMPR1 |=  (ADC_SMPR1_SMP12_2 | ADC_SMPR1_SMP12_1); // 84

    ADC1->CR2 = ADC_CR2_ADON; // включаем АЦП
}

void TIM6_config(double freq_upd) {
    RCC->APB1ENR |= RCC_APB1ENR_TIM6EN;
    TIM6->PSC  = 60 - 1;
    TIM6->ARR = (uint32_t)(1000000.0f / freq_upd) - 1U;
    TIM6->DIER = TIM_DIER_UIE;
    NVIC_EnableIRQ(TIM6_DAC_IRQn);
    TIM6->CR1  = TIM_CR1_CEN;
}

void TIM7_config(double uart_boundrate) {
    RCC->APB1ENR |= RCC_APB1ENR_TIM7EN;
    TIM7->PSC  = 60 - 1;
    TIM7->ARR  = (uint32_t)(1000000.0f / uart_boundrate) - 1U;
    TIM7->DIER = TIM_DIER_UIE;
    NVIC_EnableIRQ(TIM7_IRQn);
    TIM7->CR1  = TIM_CR1_CEN;
}

void TIM6_DAC_IRQHandler(void) {
    if (TIM6->SR & TIM_SR_UIF) {
        TIM6->SR &= ~TIM_SR_UIF;

        uint16_t d = sin_table[sin_idx++];
        if (sin_idx >= SAMPLES) sin_idx = 0;

        DAC->DHR12R1 = d;
    }
}

// TIM7: измеряем ADC и отправляем на ПК (бинарно)
void TIM7_IRQHandler(void) {
    if (TIM7->SR & TIM_SR_UIF) {
        TIM7->SR &= ~TIM_SR_UIF;

        ADC1->SR = 0;
        ADC1->CR2 |= ADC_CR2_SWSTART;
        while (!(ADC1->SR & ADC_SR_EOC)) {}
        adc_last = (uint16_t)ADC1->DR;

        USART2_send_u16_le(adc_last);
    }
}