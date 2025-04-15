/*
 * SPDX-FileCopyrightText: 2025 IObundle
 *
 * SPDX-License-Identifier: MIT
 */

#include "iob_bsp.h"
#include "iob_gpio_csrs.h"
#include "iob_printf.h"
#include "iob_pulse_gen_tester_conf.h"
#include "iob_pulse_gen_tester_mmap.h"
#include "iob_uart.h"
#include <string.h>

int main() {
  char pass_string[] = "Test passed!";
  char fail_string[] = "Test failed!";
  uint32_t gpio_output;

  // init gpio
  iob_gpio_init_baseaddr(GPIO0_BASE);

  // init uart
  uart_init(UART0_BASE, IOB_BSP_FREQ / IOB_BSP_BAUD);
  printf_init(&uart_putc);

  // Initial Tester message
  uart_puts("\nHello world from Tester of 'iob_pulse_gen' core!\n\n\n");

  uart_puts("Starting verification sequence of 'iob_pulse_gen'...\n\n");

  // Check that output of iob_pulse_gen is zero
  gpio_output = iob_gpio_get_input_0();
  if (gpio_output != 0) {
    uart_puts("ERROR: Initial output of iob_pulse_gen is non-zero!\n");
    uart_finish();
    return 1;
  }

  // Toggle enable of iob_pulse_gen
  iob_gpio_set_output_0(1);
  iob_gpio_set_output_0(0);

  // Check that output of iob_pulse_gen is enabled
  // NOTE: GPIO is not the best verification instrument for iob_pulse_gen, since
  // it is not very precise in the timing for sampling its output. Ideally we
  // should use a dedicated verification instrument that measures the timing of
  // the output of iob_pulse_gen.
  gpio_output = iob_gpio_get_input_0();
  if (gpio_output != 1) {
    uart_puts("ERROR: iob_pulse_gen did not generate output!\n");
    uart_finish();
    return 1;
  }

  uart_puts("Verification of 'iob_pulse_gen' successful!\n\n");

  //
  // End test
  //

  uart_sendfile("test.log", strlen(pass_string), pass_string);

  uart_finish();
}
