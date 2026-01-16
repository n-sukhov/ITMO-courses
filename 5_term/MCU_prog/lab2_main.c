#include <stdint.h>
#include "stm32f446xx.h"

#define PACKET_HEADER 0xAA
#define PACKET_TERMINATOR 0x55
#define SLAVE_ID 0x01

#define CMD_ECHO 0x01
#define CMD_LEDS_ALL_ON 0x02
#define CMD_LEDS_ALL_OFF 0x03
#define CMD_LED_PATTERN 0x04
#define CMD_LED_STATE 0x05
#define CMD_SET_SINGLE_LED 0x06

uint8_t rx_buffer[16];
uint8_t rx_index = 0;
uint8_t packet_length = 0;
uint8_t packet_received = 0;

uint8_t led_count = 1;

void delay(uint32_t count) {
    for(volatile uint32_t i = 0; i < count; i++);
}

void set_led_pattern(uint8_t pattern) {
    GPIOC->ODR = (GPIOC->ODR & ~(0xFF << 4)) | (pattern << 4);
}

void USART_Init(void) {
    // Включаем тактирование USART2 и GPIOA
    RCC->APB1ENR |= RCC_APB1ENR_USART2EN;
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;
    
    //Переводим GPIOA в режим альтернативной функции для использования USART
    GPIOA->MODER &= ~(GPIO_MODER_MODER2_Msk | GPIO_MODER_MODER3_Msk);
    GPIOA->MODER |= (2 << GPIO_MODER_MODER2_Pos) | (2 << GPIO_MODER_MODER3_Pos);
    
    GPIOA->AFR[0] &= ~(0xFF << (2 * 4));
    GPIOA->AFR[0] |= (7 << (2 * 4)) | (7 << (3 * 4));
    
    USART2->BRR = (104 << 4) | 3;
    
    // Включаем передатчик, приёмник и генерацию прерываний
    USART2->CR1 |= USART_CR1_TE | USART_CR1_RE | USART_CR1_RXNEIE;
    
    USART2->CR1 |= USART_CR1_UE;
    
    // Включаем прерывание USART2 в контроллере прерываний и устанавливает высший приоритет
    NVIC_EnableIRQ(USART2_IRQn);
    NVIC_SetPriority(USART2_IRQn, 0);
}

void USART2_SendChar(uint8_t ch) {
    while (!(USART2->SR & USART_SR_TXE));   
    USART2->DR = ch;
}

void USART2_SendString(char *str) {
    while (*str) {
        USART2_SendChar(*str++);
    }
}

// функция для отправки отладочной информации
void SendDebug(char *message) {
    USART2_SendString(message);
    USART2_SendString("\n");
}

// отправка пакета
void SendPacket(uint8_t command, uint8_t *data, uint8_t data_length) {
    USART2_SendChar(PACKET_HEADER);
    uint8_t total_length = 5 + data_length;
    USART2_SendChar(total_length);
    USART2_SendChar(SLAVE_ID);
    USART2_SendChar(command);
    
    for(uint8_t i = 0; i < data_length; i++) {
        USART2_SendChar(data[i]);
    }
    
    USART2_SendChar(PACKET_TERMINATOR);
}

// Обработка команд
void ProcessCommand(uint8_t command, uint8_t *data, uint8_t data_length) {
    uint8_t response_data[2];
    
    switch(command) {
        case CMD_ECHO:
            SendPacket(CMD_ECHO, data, data_length);
            break;
            
        case CMD_LEDS_ALL_ON:
            set_led_pattern(0xFF); // Все светодиоды включены
            SendPacket(CMD_LEDS_ALL_ON, data, data_length);
            break;
            
        case CMD_LEDS_ALL_OFF:
            set_led_pattern(0x00); // Все светодиоды выключены
            SendPacket(CMD_LEDS_ALL_OFF, data, data_length);
            break;
            
        case CMD_SET_SINGLE_LED:
            if(data_length >= 2) {
                uint8_t led_num = data[0];
                uint8_t led_state = data[1];
                
                if(led_num < 8) {
                    uint8_t current_pattern = (GPIOC->ODR >> 4) & 0xFF;
                    if(led_state) {
                        current_pattern |= (1 << led_num);
                    } else {
                        current_pattern &= ~(1 << led_num);
                    }
                    set_led_pattern(current_pattern);
                }
                SendPacket(CMD_SET_SINGLE_LED, data, 2);
            }
            break;
            
        case CMD_LED_STATE:
            response_data[0] = (GPIOC->ODR >> 4) & 0xFF;
            SendPacket(CMD_LED_STATE, response_data, 1);
            break;
            
        default:
            SendDebug("Unknown command");
            break;
    }
}

void USART2_IRQHandler(void) {
    if (USART2->SR & USART_SR_RXNE) {
        uint8_t received_byte = USART2->DR;
        
        if (rx_index == 0 && received_byte == PACKET_HEADER) {
            rx_buffer[rx_index++] = received_byte;
        }
        else if (rx_index == 1) {
            packet_length = received_byte;
            rx_buffer[rx_index++] = received_byte;
        }
        else if (rx_index > 1 && rx_index < sizeof(rx_buffer)) {
            rx_buffer[rx_index++] = received_byte;
            
            if (rx_index >= packet_length) {
                if (rx_buffer[rx_index - 1] == PACKET_TERMINATOR) {
                    packet_received = 1;
                } else {
                    rx_index = 0;
                }
            }
        }
        else {
            rx_index = 0;
        }
    }
}

int main(void) {
    *((uint32_t *) 0x40023830) |= 0xF;

    GPIOC->MODER &= ~(0xFFFF << 8);
    GPIOC->MODER |= (0x5555 << 8);

    GPIOC->MODER &= ~(3 << 26);
    GPIOC->PUPDR &= ~(3 << 26);
    GPIOC->PUPDR |= (1 << 26);
    
    GPIOD->MODER &= ~(3 << 4);
    GPIOD->PUPDR &= ~(3 << 4);
    GPIOD->PUPDR |= (1 << 4);

    // Инициализация USART
    USART_Init();
    
    // Инициализация светодиодов
    set_led_pattern(0x01);
    
    uint32_t last_button1 = 1;
    uint32_t last_button2 = 1;

    while (1) {
        // Обработка пакетов USART
        if (packet_received) {
            if (rx_buffer[2] == SLAVE_ID) {
                uint8_t command = rx_buffer[3];
                uint8_t data_length = packet_length - 5;
                ProcessCommand(command, &rx_buffer[4], data_length);
            }
            
            rx_index = 0;
            packet_received = 0;
            packet_length = 0;
        }
        
        uint32_t button1 = (GPIOC->IDR >> 13) & 1;
        uint32_t button2 = (GPIOD->IDR >> 2) & 1;
           
        // Обработка нажатия синей кнопки (добавляем светодиоды слева)
        if (button1 == 0 && last_button1 == 1) {
            led_count = led_count < 8 ? led_count + 1 : 1;
            uint8_t pattern = (0xFF << (8 - led_count)) & 0xFF;
            set_led_pattern(pattern);
            delay(200000);
        }
        
        // Обработка нажатия красной кнопки (убираем светодиоды слева)
        if (button2 == 0 && last_button2 == 1) {
            led_count = led_count > 1 ? led_count - 1 : 8;
            uint8_t pattern = (0xFF << (8 - led_count)) & 0xFF;
            set_led_pattern(pattern);
            delay(200000);
        }
        
        last_button1 = button1;
        last_button2 = button2;
        
        delay(10000);
    }
}