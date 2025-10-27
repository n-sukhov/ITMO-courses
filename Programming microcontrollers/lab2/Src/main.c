#include <stdint.h>

#define GPIOC_BASE 0x40020800
#define GPIOD_BASE 0x40020C00

typedef struct {
    uint32_t MODER;
    uint32_t OTYPER;
    uint32_t OSPEEDR;
    uint32_t PUPDR;
    uint32_t IDR;
    uint32_t ODR;
    uint32_t BSRR;
    uint32_t LCKR;
    uint32_t AFR[2];
} GPIO_TypeDef;

#define GPIOC ((GPIO_TypeDef *)GPIOC_BASE)
#define GPIOD ((GPIO_TypeDef *)GPIOD_BASE)

void delay(uint32_t count) {
  for(volatile uint32_t i = 0; i < count; i++);
}

int main(void) {
  *((uint32_t *) 0x40023830) |= 0xF; // Включаем тактирование для GPIOA-D

  // Устанавливаем пины 4-11 на выход
  GPIOC->MODER &= ~(0xFFFF << 8);
  GPIOC->MODER |= (0x5555 << 8);

  // Обе кнопки - активный низкий
  GPIOC->MODER &= ~(3 << 26);
  GPIOC->PUPDR &= ~(3 << 26);
  GPIOC->PUPDR |= (1 << 26); // При нажатии кнопки устанавливается 0
  
  GPIOD->MODER &= ~(3 << 4);
  GPIOD->PUPDR &= ~(3 << 4);
  GPIOD->PUPDR |= (1 << 4);
  
  uint8_t led_position = 0;
  uint32_t last_button1 = 1;
  uint32_t last_button2 = 1;
  
  // Инициализация светодиодов
  GPIOC->ODR &= ~(0xFF << 4); // Устанавливаются в 0 с 4 по 11
  GPIOC->ODR |= (1 << (4 + led_position)); // Устанавливаем в 1 светодиод на позиции

  for (;;) {
    // Читаем значения на пинах, к которым подключены кнопки
    uint32_t button1 = (GPIOC->IDR >> 13) & 1;
    uint32_t button2 = (GPIOD->IDR >> 2) & 1;
    
    if (button1 == 0 && last_button1 == 1) {
      led_position = (led_position == 0) ? 7 : (led_position - 1);
      delay(100000);  
    }
    
    if (button2 == 0 && last_button2 == 1) {
      led_position = (led_position + 1) % 8;
      delay(100000);  
    }
    
    last_button1 = button1;
    last_button2 = button2;
    
    // Обновляем светодиоды
    GPIOC->ODR &= ~(0xFF << 4);
    GPIOC->ODR |= (1 << (4 + led_position));
    
    delay(10000);
  }
}
