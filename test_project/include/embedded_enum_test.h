#ifndef EMBEDDED_ENUM_TEST_H
#define EMBEDDED_ENUM_TEST_H

/* following defines should be used for structure members */
#define __IM volatile const /*! Defines 'read only' structure member permissions */
#define __OM volatile       /*! Defines 'write only' structure member permissions */
#define __IOM volatile      /*! Defines 'read / write' structure member permissions */

typedef int uint32_t;

typedef struct
{ /*!< (@ 0x48000A00) GPIOF Structure*/

    union
    {
        __IOM uint32_t MODER; /*!< (@ 0x00000000) GPIO port mode register  */

        struct
        {
            __IOM uint32_t MODER0 : 2;  /*!< [1..0] Port x configuration bits (y = 0..15)   */
            __IOM uint32_t MODER1 : 2;  /*!< [3..2] Port x configuration bits (y = 0..15)   */
            __IOM uint32_t MODER2 : 2;  /*!< [5..4] Port x configuration bits (y = 0..15)   */
            __IOM uint32_t MODER3 : 2;  /*!< [7..6] Port x configuration bits (y = 0..15)   */
            __IOM uint32_t MODER4 : 2;  /*!< [9..8] Port x configuration bits (y = 0..15)   */
            __IOM uint32_t MODER5 : 2;  /*!< [11..10] Port x configuration bits (y = 0..15) */
            __IOM uint32_t MODER6 : 2;  /*!< [13..12] Port x configuration bits (y = 0..15) */
            __IOM uint32_t MODER7 : 2;  /*!< [15..14] Port x configuration bits (y = 0..15) */
            __IOM uint32_t MODER8 : 2;  /*!< [17..16] Port x configuration bits (y = 0..15) */
            __IOM uint32_t MODER9 : 2;  /*!< [19..18] Port x configuration bits (y = 0..15) */
            __IOM uint32_t MODER10 : 2; /*!< [21..20] Port x configuration bits (y = 0..15) */
            __IOM uint32_t MODER11 : 2; /*!< [23..22] Port x configuration bits (y = 0..15) */
            __IOM uint32_t MODER12 : 2; /*!< [25..24] Port x configuration bits (y = 0..15) */
            __IOM uint32_t MODER13 : 2; /*!< [27..26] Port x configuration bits (y = 0..15) */
            __IOM uint32_t MODER14 : 2; /*!< [29..28] Port x configuration bits (y = 0..15) */
            __IOM uint32_t MODER15 : 2; /*!< [31..30] Port x configuration bits (y = 0..15) */
        } MODER_b;
    };

    union
    {
        union
        {
            __IM uint32_t OD; /*!< (@ 0x00000004) GPIO port open drain bit set/reset register */

            struct
            {
                __IM uint32_t OD0 : 1;  /*!< [0..0] Port x open drain configuration bits (y = 0..15)  */
                __IM uint32_t OD1 : 1;  /*!< [1..1] Port x open drain configuration bits (y = 0..15)  */
                __IM uint32_t OD2 : 1;  /*!< [2..2] Port x open drain configuration bits (y = 0..15)  */
                __IM uint32_t OD3 : 1;  /*!< [3..3] Port x open drain configuration bits (y = 0..15)  */
                __IM uint32_t OD4 : 1;  /*!< [4..4] Port x open drain configuration bits (y = 0..15)  */
                __IM uint32_t OD5 : 1;  /*!< [5..5] Port x open drain configuration bits (y = 0..15)  */
                __IM uint32_t OD6 : 1;  /*!< [6..6] Port x open drain configuration bits (y = 0..15)  */
                __IM uint32_t OD7 : 1;  /*!< [7..7] Port x open drain configuration bits (y = 0..15)  */
                __IM uint32_t OD8 : 1;  /*!< [8..8] Port x open drain configuration bits (y = 0..15)  */
                __IM uint32_t OD9 : 1;  /*!< [9..9] Port x open drain configuration bits (y = 0..15)  */
                __IM uint32_t OD10 : 1; /*!< [10..10] Port x open drain configuration bits (y = 0..15)*/
                __IM uint32_t OD11 : 1; /*!< [11..11] Port x open drain configuration bits (y = 0..15)*/
                __IM uint32_t OD12 : 1; /*!< [12..12] Port x open drain configuration bits (y = 0..15)*/
                __IM uint32_t OD13 : 1; /*!< [13..13] Port x open drain configuration bits (y = 0..15)*/
                __IM uint32_t OD14 : 1; /*!< [14..14] Port x open drain configuration bits (y = 0..15)*/
                __IM uint32_t OD15 : 1; /*!< [15..15] Port x open drain configuration bits (y = 0..15)*/
            } OD_b;
        };

        union
        {
            __IOM uint32_t OD_BSRR; /*!< (@ 0x00000004) GPIO port open drain bit set/reset register */

            struct
            {
                __IOM uint32_t BS0 : 1;  /*!< [0..0] Port x open drain configuration set bits (y = 0..15)*/
                __IOM uint32_t BS1 : 1;  /*!< [1..1] Port x open drain configuration set bits (y = 0..15)*/
                __IOM uint32_t BS2 : 1;  /*!< [2..2] Port x open drain configuration set bits (y = 0..15)*/
                __IOM uint32_t BS3 : 1;  /*!< [3..3] Port x open drain configuration set bits (y = 0..15)*/
                __IOM uint32_t BS4 : 1;  /*!< [4..4] Port x open drain configuration set bits (y = 0..15)*/
                __IOM uint32_t BS5 : 1;  /*!< [5..5] Port x open drain configuration set bits (y = 0..15)*/
                __IOM uint32_t BS6 : 1;  /*!< [6..6] Port x open drain configuration set bits (y = 0..15)*/
                __IOM uint32_t BS7 : 1;  /*!< [7..7] Port x open drain configuration set bits (y = 0..15)*/
                __IOM uint32_t BS8 : 1;  /*!< [8..8] Port x open drain configuration set bits (y = 0..15)*/
                __IOM uint32_t BS9 : 1;  /*!< [9..9] Port x open drain configuration set bits (y = 0..15)*/
                __IOM uint32_t BS10 : 1; /*!< [10..10] Port x open drain configuration set bits (y = 0..15)   */
                __IOM uint32_t BS11 : 1; /*!< [11..11] Port x open drain configuration set bits (y = 0..15)   */
                __IOM uint32_t BS12 : 1; /*!< [12..12] Port x open drain configuration set bits (y = 0..15)   */
                __IOM uint32_t BS13 : 1; /*!< [13..13] Port x open drain configuration set bits (y = 0..15)   */
                __IOM uint32_t BS14 : 1; /*!< [14..14] Port x open drain configuration set bits (y = 0..15)   */
                __IOM uint32_t BS15 : 1; /*!< [15..15] Port x open drain configuration set bits (y = 0..15)   */
                __IOM uint32_t BR0 : 1;  /*!< [16..16] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR1 : 1;  /*!< [17..17] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR2 : 1;  /*!< [18..18] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR3 : 1;  /*!< [19..19] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR4 : 1;  /*!< [20..20] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR5 : 1;  /*!< [21..21] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR6 : 1;  /*!< [22..22] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR7 : 1;  /*!< [23..23] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR8 : 1;  /*!< [24..24] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR9 : 1;  /*!< [25..25] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR10 : 1; /*!< [26..26] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR11 : 1; /*!< [27..27] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR12 : 1; /*!< [28..28] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR13 : 1; /*!< [29..29] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR14 : 1; /*!< [30..30] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR15 : 1; /*!< [31..31] Port x open drain configuration reset bits (y = 0..15) */
            } OD_BSRR_b;
        };
    };

    union
    {
        union
        {
            __IM uint32_t SR; /*!< (@ 0x00000008) GPIO port slew rate bit set/reset register*/

            struct
            {
                __IM uint32_t SR0 : 1;  /*!< [0..0] Port x open drain configuration reset bits (y = 0..15)   */
                __IM uint32_t SR1 : 1;  /*!< [1..1] Port x open drain configuration reset bits (y = 0..15)   */
                __IM uint32_t SR2 : 1;  /*!< [2..2] Port x open drain configuration reset bits (y = 0..15)   */
                __IM uint32_t SR3 : 1;  /*!< [3..3] Port x open drain configuration reset bits (y = 0..15)   */
                __IM uint32_t SR4 : 1;  /*!< [4..4] Port x open drain configuration reset bits (y = 0..15)   */
                __IM uint32_t SR5 : 1;  /*!< [5..5] Port x open drain configuration reset bits (y = 0..15)   */
                __IM uint32_t SR6 : 1;  /*!< [6..6] Port x open drain configuration reset bits (y = 0..15)   */
                __IM uint32_t SR7 : 1;  /*!< [7..7] Port x open drain configuration reset bits (y = 0..15)   */
                __IM uint32_t SR8 : 1;  /*!< [8..8] Port x open drain configuration reset bits (y = 0..15)   */
                __IM uint32_t SR9 : 1;  /*!< [9..9] Port x open drain configuration reset bits (y = 0..15)   */
                __IM uint32_t SR10 : 1; /*!< [10..10] Port x open drain configuration reset bits (y = 0..15) */
                __IM uint32_t SR11 : 1; /*!< [11..11] Port x open drain configuration reset bits (y = 0..15) */
                __IM uint32_t SR12 : 1; /*!< [12..12] Port x open drain configuration reset bits (y = 0..15) */
                __IM uint32_t SR13 : 1; /*!< [13..13] Port x open drain configuration reset bits (y = 0..15) */
                __IM uint32_t SR14 : 1; /*!< [14..14] Port x open drain configuration reset bits (y = 0..15) */
                __IM uint32_t SR15 : 1; /*!< [15..15] Port x open drain configuration reset bits (y = 0..15) */
            } SR_b;
        };

        union
        {
            __IOM uint32_t SR_BSRR; /*!< (@ 0x00000008) GPIO port slew rate bit set/reset register*/

            struct
            {
                __IOM uint32_t BS0 : 1;  /*!< [0..0] Port x slew rate configuration bits (y = 0..15)   */
                __IOM uint32_t BS1 : 1;  /*!< [1..1] Port x slew rate configuration bits (y = 0..15)   */
                __IOM uint32_t BS2 : 1;  /*!< [2..2] Port x slew rate configuration bits (y = 0..15)   */
                __IOM uint32_t BS3 : 1;  /*!< [3..3] Port x slew rate configuration bits (y = 0..15)   */
                __IOM uint32_t BS4 : 1;  /*!< [4..4] Port x slew rate configuration bits (y = 0..15)   */
                __IOM uint32_t BS5 : 1;  /*!< [5..5] Port x slew rate configuration bits (y = 0..15)   */
                __IOM uint32_t BS6 : 1;  /*!< [6..6] Port x slew rate configuration bits (y = 0..15)   */
                __IOM uint32_t BS7 : 1;  /*!< [7..7] Port x slew rate configuration bits (y = 0..15)   */
                __IOM uint32_t BS8 : 1;  /*!< [8..8] Port x slew rate configuration bits (y = 0..15)   */
                __IOM uint32_t BS9 : 1;  /*!< [9..9] Port x slew rate configuration bits (y = 0..15)   */
                __IOM uint32_t BS10 : 1; /*!< [10..10] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BS11 : 1; /*!< [11..11] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BS12 : 1; /*!< [12..12] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BS13 : 1; /*!< [13..13] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BS14 : 1; /*!< [14..14] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BS15 : 1; /*!< [15..15] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR0 : 1;  /*!< [16..16] Port x slew rate configuration reset bits (y = 0..15)  */
                __IOM uint32_t BR1 : 1;  /*!< [17..17] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR2 : 1;  /*!< [18..18] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR3 : 1;  /*!< [19..19] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR4 : 1;  /*!< [20..20] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR5 : 1;  /*!< [21..21] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR6 : 1;  /*!< [22..22] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR7 : 1;  /*!< [23..23] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR8 : 1;  /*!< [24..24] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR9 : 1;  /*!< [25..25] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR10 : 1; /*!< [26..26] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR11 : 1; /*!< [27..27] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR12 : 1; /*!< [28..28] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR13 : 1; /*!< [29..29] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR14 : 1; /*!< [30..30] Port x open drain configuration reset bits (y = 0..15) */
                __IOM uint32_t BR15 : 1; /*!< [31..31] Port x open drain configuration reset bits (y = 0..15) */
            } SR_BSRR_b;
        };
    };

    union
    {
        union
        {
            __IM uint32_t PU; /*!< (@ 0x0000000C) GPIO port pull up bit set/reset register  */

            struct
            {
                __IM uint32_t PU0 : 1;  /*!< [0..0] Port x pull up configuration bits (y = 0..15)*/
                __IM uint32_t PU1 : 1;  /*!< [1..1] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PU2 : 1;  /*!< [2..2] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PU3 : 1;  /*!< [3..3] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PU4 : 1;  /*!< [4..4] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PU5 : 1;  /*!< [5..5] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PU6 : 1;  /*!< [6..6] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PU7 : 1;  /*!< [7..7] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PU8 : 1;  /*!< [8..8] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PU9 : 1;  /*!< [9..9] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PU10 : 1; /*!< [10..10] Port x slew rate configuration bits (y = 0..15) */
                __IM uint32_t PU11 : 1; /*!< [11..11] Port x slew rate configuration bits (y = 0..15) */
                __IM uint32_t PU12 : 1; /*!< [12..12] Port x slew rate configuration bits (y = 0..15) */
                __IM uint32_t PU13 : 1; /*!< [13..13] Port x slew rate configuration bits (y = 0..15) */
                __IM uint32_t PU14 : 1; /*!< [14..14] Port x slew rate configuration bits (y = 0..15) */
                __IM uint32_t PU15 : 1; /*!< [15..15] Port x slew rate configuration bits (y = 0..15) */
            } PU_b;
        };

        union
        {
            __IOM uint32_t PU_BSRR; /*!< (@ 0x0000000C) GPIO port pull up bit set/reset register  */

            struct
            {
                __IOM uint32_t BS0 : 1;  /*!< [0..0] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS1 : 1;  /*!< [1..1] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS2 : 1;  /*!< [2..2] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS3 : 1;  /*!< [3..3] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS4 : 1;  /*!< [4..4] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS5 : 1;  /*!< [5..5] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS6 : 1;  /*!< [6..6] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS7 : 1;  /*!< [7..7] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS8 : 1;  /*!< [8..8] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS9 : 1;  /*!< [9..9] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS10 : 1; /*!< [10..10] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS11 : 1; /*!< [11..11] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS12 : 1; /*!< [12..12] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS13 : 1; /*!< [13..13] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS14 : 1; /*!< [14..14] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS15 : 1; /*!< [15..15] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BR0 : 1;  /*!< [16..16] Port x pull up configuration reset bits (y = 0..15)    */
                __IOM uint32_t BR1 : 1;  /*!< [17..17] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR2 : 1;  /*!< [18..18] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR3 : 1;  /*!< [19..19] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR4 : 1;  /*!< [20..20] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR5 : 1;  /*!< [21..21] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR6 : 1;  /*!< [22..22] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR7 : 1;  /*!< [23..23] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR8 : 1;  /*!< [24..24] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR9 : 1;  /*!< [25..25] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR10 : 1; /*!< [26..26] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR11 : 1; /*!< [27..27] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR12 : 1; /*!< [28..28] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR13 : 1; /*!< [29..29] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR14 : 1; /*!< [30..30] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR15 : 1; /*!< [31..31] Port x slew rate configuration bits (y = 0..15) */
            } PU_BSRR_b;
        };
    };

    union
    {
        union
        {
            __IM uint32_t PD; /*!< (@ 0x00000010) GPIO port pull down bit set/reset register*/

            struct
            {
                __IM uint32_t PD0 : 1;  /*!< [0..0] Port x pull down configuration bits (y = 0..15)   */
                __IM uint32_t PD1 : 1;  /*!< [1..1] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PD2 : 1;  /*!< [2..2] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PD3 : 1;  /*!< [3..3] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PD4 : 1;  /*!< [4..4] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PD5 : 1;  /*!< [5..5] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PD6 : 1;  /*!< [6..6] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PD7 : 1;  /*!< [7..7] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PD8 : 1;  /*!< [8..8] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PD9 : 1;  /*!< [9..9] Port x slew rate configuration bits (y = 0..15)   */
                __IM uint32_t PD10 : 1; /*!< [10..10] Port x slew rate configuration bits (y = 0..15) */
                __IM uint32_t PD11 : 1; /*!< [11..11] Port x slew rate configuration bits (y = 0..15) */
                __IM uint32_t PD12 : 1; /*!< [12..12] Port x slew rate configuration bits (y = 0..15) */
                __IM uint32_t PD13 : 1; /*!< [13..13] Port x slew rate configuration bits (y = 0..15) */
                __IM uint32_t PD14 : 1; /*!< [14..14] Port x slew rate configuration bits (y = 0..15) */
                __IM uint32_t PD15 : 1; /*!< [15..15] Port x slew rate configuration bits (y = 0..15) */
            } PD_b;
        };

        union
        {
            __IOM uint32_t PD_BSRR; /*!< (@ 0x00000010) GPIO port pull down bit set/reset register*/

            struct
            {
                __IOM uint32_t BS0 : 1;  /*!< [0..0] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS1 : 1;  /*!< [1..1] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS2 : 1;  /*!< [2..2] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS3 : 1;  /*!< [3..3] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS4 : 1;  /*!< [4..4] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS5 : 1;  /*!< [5..5] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS6 : 1;  /*!< [6..6] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS7 : 1;  /*!< [7..7] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS8 : 1;  /*!< [8..8] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS9 : 1;  /*!< [9..9] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS10 : 1; /*!< [10..10] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS11 : 1; /*!< [11..11] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS12 : 1; /*!< [12..12] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS13 : 1; /*!< [13..13] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS14 : 1; /*!< [14..14] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BS15 : 1; /*!< [15..15] Port x pull up configuration set bits (y = 0..15) */
                __IOM uint32_t BR0 : 1;  /*!< [16..16] Port x pull up configuration reset bits (y = 0..15)    */
                __IOM uint32_t BR1 : 1;  /*!< [17..17] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR2 : 1;  /*!< [18..18] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR3 : 1;  /*!< [19..19] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR4 : 1;  /*!< [20..20] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR5 : 1;  /*!< [21..21] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR6 : 1;  /*!< [22..22] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR7 : 1;  /*!< [23..23] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR8 : 1;  /*!< [24..24] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR9 : 1;  /*!< [25..25] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR10 : 1; /*!< [26..26] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR11 : 1; /*!< [27..27] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR12 : 1; /*!< [28..28] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR13 : 1; /*!< [29..29] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR14 : 1; /*!< [30..30] Port x slew rate configuration bits (y = 0..15) */
                __IOM uint32_t BR15 : 1; /*!< [31..31] Port x slew rate configuration bits (y = 0..15) */
            };
        };
    };

    union
    {
        __IOM uint32_t IDR; /*!< (@ 0x00000014) GPIO port input data register   */

        struct
        {
            __IOM uint32_t IDR0 : 1;  /*!< [0..0] Port x pull up configuration reset bits (y = 0..15) */
            __IOM uint32_t IDR1 : 1;  /*!< [1..1] Port x slew rate configuration bits (y = 0..15)   */
            __IOM uint32_t IDR2 : 1;  /*!< [2..2] Port x slew rate configuration bits (y = 0..15)   */
            __IOM uint32_t IDR3 : 1;  /*!< [3..3] Port x slew rate configuration bits (y = 0..15)   */
            __IOM uint32_t IDR4 : 1;  /*!< [4..4] Port x slew rate configuration bits (y = 0..15)   */
            __IOM uint32_t IDR5 : 1;  /*!< [5..5] Port x slew rate configuration bits (y = 0..15)   */
            __IOM uint32_t IDR6 : 1;  /*!< [6..6] Port x slew rate configuration bits (y = 0..15)   */
            __IOM uint32_t IDR7 : 1;  /*!< [7..7] Port x slew rate configuration bits (y = 0..15)   */
            __IOM uint32_t IDR8 : 1;  /*!< [8..8] Port x slew rate configuration bits (y = 0..15)   */
            __IOM uint32_t IDR9 : 1;  /*!< [9..9] Port x slew rate configuration bits (y = 0..15)   */
            __IOM uint32_t IDR10 : 1; /*!< [10..10] Port x slew rate configuration bits (y = 0..15) */
            __IOM uint32_t IDR11 : 1; /*!< [11..11] Port x slew rate configuration bits (y = 0..15) */
            __IOM uint32_t IDR12 : 1; /*!< [12..12] Port x slew rate configuration bits (y = 0..15) */
            __IOM uint32_t IDR13 : 1; /*!< [13..13] Port x slew rate configuration bits (y = 0..15) */
            __IOM uint32_t IDR14 : 1; /*!< [14..14] Port x slew rate configuration bits (y = 0..15) */
            __IOM uint32_t IDR15 : 1; /*!< [15..15] Port x slew rate configuration bits (y = 0..15) */
        } IDR_b;
    };

    union
    {
        __IOM uint32_t ODR; /*!< (@ 0x00000018) GPIO port output data register  */

        struct
        {
            __IOM uint32_t ODR0 : 1;  /*!< [0..0] ODR0  */
            __IOM uint32_t ODR1 : 1;  /*!< [1..1] ODR1  */
            __IOM uint32_t ODR2 : 1;  /*!< [2..2] ODR2  */
            __IOM uint32_t ODR3 : 1;  /*!< [3..3] ODR3  */
            __IOM uint32_t ODR4 : 1;  /*!< [4..4] ODR4  */
            __IOM uint32_t ODR5 : 1;  /*!< [5..5] ODR5  */
            __IOM uint32_t ODR6 : 1;  /*!< [6..6] ODR6  */
            __IOM uint32_t ODR7 : 1;  /*!< [7..7] ODR7  */
            __IOM uint32_t ODR8 : 1;  /*!< [8..8] ODR8  */
            __IOM uint32_t ODR9 : 1;  /*!< [9..9] ODR9  */
            __IOM uint32_t ODR10 : 1; /*!< [10..10] ODR10 */
            __IOM uint32_t ODR11 : 1; /*!< [11..11] ODR11 */
            __IOM uint32_t ODR12 : 1; /*!< [12..12] ODR12 */
            __IOM uint32_t ODR13 : 1; /*!< [13..13] ODR13 */
            __IOM uint32_t ODR14 : 1; /*!< [14..14] ODR14 */
            __IOM uint32_t ODR15 : 1; /*!< [15..15] ODR15 */
        } ODR_b;
    };

    union
    {
        __IOM uint32_t BSRR; /*!< (@ 0x0000001C) GPIO bit set reset register*/

        struct
        {
            __IOM uint32_t BS0 : 1;  /*!< [0..0] BS0   */
            __IOM uint32_t BS1 : 1;  /*!< [1..1] BS1   */
            __IOM uint32_t BS2 : 1;  /*!< [2..2] BS2   */
            __IOM uint32_t BS3 : 1;  /*!< [3..3] BS3   */
            __IOM uint32_t BS4 : 1;  /*!< [4..4] BS4   */
            __IOM uint32_t BS5 : 1;  /*!< [5..5] BS5   */
            __IOM uint32_t BS6 : 1;  /*!< [6..6] BS6   */
            __IOM uint32_t BS7 : 1;  /*!< [7..7] BS7   */
            __IOM uint32_t BS8 : 1;  /*!< [8..8] BS8   */
            __IOM uint32_t BS9 : 1;  /*!< [9..9] BS9   */
            __IOM uint32_t BS10 : 1; /*!< [10..10] BS10*/
            __IOM uint32_t BS11 : 1; /*!< [11..11] BS11*/
            __IOM uint32_t BS12 : 1; /*!< [12..12] BS12*/
            __IOM uint32_t BS13 : 1; /*!< [13..13] BS13*/
            __IOM uint32_t BS14 : 1; /*!< [14..14] BS14*/
            __IOM uint32_t BS15 : 1; /*!< [15..15] BS15*/
            __IOM uint32_t BR0 : 1;  /*!< [16..16] BR0 */
            __IOM uint32_t BR1 : 1;  /*!< [17..17] BR1 */
            __IOM uint32_t BR2 : 1;  /*!< [18..18] BR2 */
            __IOM uint32_t BR3 : 1;  /*!< [19..19] BR3 */
            __IOM uint32_t BR4 : 1;  /*!< [20..20] BR4 */
            __IOM uint32_t BR5 : 1;  /*!< [21..21] BR5 */
            __IOM uint32_t BR6 : 1;  /*!< [22..22] BR6 */
            __IOM uint32_t BR7 : 1;  /*!< [23..23] BR7 */
            __IOM uint32_t BR8 : 1;  /*!< [24..24] BR8 */
            __IOM uint32_t BR9 : 1;  /*!< [25..25] BR9 */
            __IOM uint32_t BR10 : 1; /*!< [26..26] BR10*/
            __IOM uint32_t BR11 : 1; /*!< [27..27] BR11*/
            __IOM uint32_t BR12 : 1; /*!< [28..28] BR12*/
            __IOM uint32_t BR13 : 1; /*!< [29..29] BR13*/
            __IOM uint32_t BR14 : 1; /*!< [30..30] BR14*/
            __IOM uint32_t BR15 : 1; /*!< [31..31] BR15*/
        } BSRR_b;
    };

    union
    {
        __IOM uint32_t LCKR; /*!< (@ 0x00000020) GPIO lock register  */

        struct
        {
            __IOM uint32_t LCK0 : 1;  /*!< [0..0] LCK0  */
            __IOM uint32_t LCK1 : 1;  /*!< [1..1] LCK1  */
            __IOM uint32_t LCK2 : 1;  /*!< [2..2] LCK2  */
            __IOM uint32_t LCK3 : 1;  /*!< [3..3] LCK3  */
            __IOM uint32_t LCK4 : 1;  /*!< [4..4] LCK4  */
            __IOM uint32_t LCK5 : 1;  /*!< [5..5] LCK5  */
            __IOM uint32_t LCK6 : 1;  /*!< [6..6] LCK6  */
            __IOM uint32_t LCK7 : 1;  /*!< [7..7] LCK7  */
            __IOM uint32_t LCK8 : 1;  /*!< [8..8] LCK8  */
            __IOM uint32_t LCK9 : 1;  /*!< [9..9] LCK9  */
            __IOM uint32_t LCK10 : 1; /*!< [10..10] LCK10 */
            __IOM uint32_t LCK11 : 1; /*!< [11..11] LCK11 */
            __IOM uint32_t LCK12 : 1; /*!< [12..12] LCK12 */
            __IOM uint32_t LCK13 : 1; /*!< [13..13] LCK13 */
            __IOM uint32_t LCK14 : 1; /*!< [14..14] LCK14 */
            __IOM uint32_t LCK15 : 1; /*!< [15..15] LCK15 */
            __IOM uint32_t LCKK : 1;  /*!< [16..16] LCKK*/
        } LCKR_b;
    };

    union
    {
        __IOM uint32_t AFRL; /*!< (@ 0x00000024) GPIO AF register    */

        struct
        {
            __IOM uint32_t AFR0 : 4; /*!< [3..0] AFR0  */
            __IOM uint32_t AFR1 : 4; /*!< [7..4] AFR1  */
            __IOM uint32_t AFR2 : 4; /*!< [11..8] AFR2 */
            __IOM uint32_t AFR3 : 4; /*!< [15..12] AFR3*/
            __IOM uint32_t AFR4 : 4; /*!< [19..16] AFR4*/
            __IOM uint32_t AFR5 : 4; /*!< [23..20] AFR5*/
            __IOM uint32_t AFR6 : 4; /*!< [27..24] AFR6*/
            __IOM uint32_t AFR7 : 4; /*!< [31..28] AFR7*/
        } AFRL_b;
    };

    union
    {
        __IOM uint32_t AFRH; /*!< (@ 0x00000028) GPIO AF register    */

        struct
        {
            __IOM uint32_t AFR8 : 4;  /*!< [3..0] AFR8  */
            __IOM uint32_t AFR9 : 4;  /*!< [7..4] AFR9  */
            __IOM uint32_t AFR10 : 4; /*!< [11..8] AFR10*/
            __IOM uint32_t AFR11 : 4; /*!< [15..12] AFR11 */
            __IOM uint32_t AFR12 : 4; /*!< [19..16] AFR12 */
            __IOM uint32_t AFR13 : 4; /*!< [23..20] AFR13 */
            __IOM uint32_t AFR14 : 4; /*!< [27..24] AFR14 */
            __IOM uint32_t AFR15 : 4; /*!< [31..28] AFR15 */
        } AFRH_b;
    };

    union
    {
        __IOM uint32_t BTGLR; /*!< (@ 0x0000002C) GPIO output bit troggle  */

        struct
        {
            __IOM uint32_t BTGL0 : 1;  /*!< [0..0] BTGL0 */
            __IOM uint32_t BTGL1 : 1;  /*!< [1..1] BTGL1 */
            __IOM uint32_t BTGL2 : 1;  /*!< [2..2] BTGL2 */
            __IOM uint32_t BTGL3 : 1;  /*!< [3..3] BTGL3 */
            __IOM uint32_t BTGL4 : 1;  /*!< [4..4] BTGL4 */
            __IOM uint32_t BTGL5 : 1;  /*!< [5..5] BTGL5 */
            __IOM uint32_t BTGL6 : 1;  /*!< [6..6] BTGL6 */
            __IOM uint32_t BTGL7 : 1;  /*!< [7..7] BTGL7 */
            __IOM uint32_t BTGL8 : 1;  /*!< [8..8] BTGL8 */
            __IOM uint32_t BTGL9 : 1;  /*!< [9..9] BTGL9 */
            __IOM uint32_t BTGL10 : 1; /*!< [10..10] BTGL10*/
            __IOM uint32_t BTGL11 : 1; /*!< [11..11] BTGL11*/
            __IOM uint32_t BTGL12 : 1; /*!< [12..12] BTGL12*/
            __IOM uint32_t BTGL13 : 1; /*!< [13..13] BTGL13*/
            __IOM uint32_t BTGL14 : 1; /*!< [14..14] BTGL14*/
            __IOM uint32_t BTGL15 : 1; /*!< [15..15] BTGL15*/
        } BTGLR_b;
    };

    union
    {
        union
        {
            __IOM uint32_t DR_BSRR; /*!< (@ 0x00000030) GPIO port driving strength bit set/reset register*/

            struct
            {
                __IOM uint32_t BS0 : 1;  /*!< [0..0] BS0   */
                __IOM uint32_t BS1 : 1;  /*!< [1..1] BS1   */
                __IOM uint32_t BS2 : 1;  /*!< [2..2] BS2   */
                __IOM uint32_t BS3 : 1;  /*!< [3..3] BS3   */
                __IOM uint32_t BS4 : 1;  /*!< [4..4] BS4   */
                __IOM uint32_t BS5 : 1;  /*!< [5..5] BS5   */
                __IOM uint32_t BS6 : 1;  /*!< [6..6] BS6   */
                __IOM uint32_t BS7 : 1;  /*!< [7..7] BS7   */
                __IOM uint32_t BS8 : 1;  /*!< [8..8] BS8   */
                __IOM uint32_t BS9 : 1;  /*!< [9..9] BS9   */
                __IOM uint32_t BS10 : 1; /*!< [10..10] BS10*/
                __IOM uint32_t BS11 : 1; /*!< [11..11] BS11*/
                __IOM uint32_t BS12 : 1; /*!< [12..12] BS12*/
                __IOM uint32_t BS13 : 1; /*!< [13..13] BS13*/
                __IOM uint32_t BS14 : 1; /*!< [14..14] BS14*/
                __IOM uint32_t BS15 : 1; /*!< [15..15] BS15*/
                __IOM uint32_t BR0 : 1;  /*!< [16..16] BR0 */
                __IOM uint32_t BR1 : 1;  /*!< [17..17] BR1 */
                __IOM uint32_t BR2 : 1;  /*!< [18..18] BR2 */
                __IOM uint32_t BR3 : 1;  /*!< [19..19] BR3 */
                __IOM uint32_t BR4 : 1;  /*!< [20..20] BR4 */
                __IOM uint32_t BR5 : 1;  /*!< [21..21] BR5 */
                __IOM uint32_t BR6 : 1;  /*!< [22..22] BR6 */
                __IOM uint32_t BR7 : 1;  /*!< [23..23] BR7 */
                __IOM uint32_t BR8 : 1;  /*!< [24..24] BR8 */
                __IOM uint32_t BR9 : 1;  /*!< [25..25] BR9 */
                __IOM uint32_t BR10 : 1; /*!< [26..26] BR10*/
                __IOM uint32_t BR11 : 1; /*!< [27..27] BR11*/
                __IOM uint32_t BR12 : 1; /*!< [28..28] BR12*/
                __IOM uint32_t BR13 : 1; /*!< [29..29] BR13*/
                __IOM uint32_t BR14 : 1; /*!< [30..30] BR14*/
                __IOM uint32_t BR15 : 1; /*!< [31..31] BR15*/
            } DR_BSRR_b;
        };

        union
        {
            __IM uint32_t DR; /*!< (@ 0x00000030) return GPIO port driving strength when read */

            struct
            {
                __IM uint32_t DR0 : 1;  /*!< [0..0] DR0   */
                __IM uint32_t DR1 : 1;  /*!< [1..1] DR1   */
                __IM uint32_t DR2 : 1;  /*!< [2..2] DR2   */
                __IM uint32_t DR3 : 1;  /*!< [3..3] DR3   */
                __IM uint32_t DR4 : 1;  /*!< [4..4] DR4   */
                __IM uint32_t DR5 : 1;  /*!< [5..5] DR5   */
                __IM uint32_t DR6 : 1;  /*!< [6..6] DR6   */
                __IM uint32_t DR7 : 1;  /*!< [7..7] DR7   */
                __IM uint32_t DR8 : 1;  /*!< [8..8] DR8   */
                __IM uint32_t DR9 : 1;  /*!< [9..9] DR9   */
                __IM uint32_t DR10 : 1; /*!< [10..10] DR10*/
                __IM uint32_t DR11 : 1; /*!< [11..11] DR11*/
                __IM uint32_t DR12 : 1; /*!< [12..12] DR12*/
                __IM uint32_t DR13 : 1; /*!< [13..13] DR13*/
                __IM uint32_t DR14 : 1; /*!< [14..14] DR14*/
                __IM uint32_t DR15 : 1; /*!< [15..15] DR15*/
            } DR_b;
        };
    };

    union
    {
        union
        {
            __IOM uint32_t CS_BSRR; /*!< (@ 0x00000034) GPIO port cmos/schmitt bit set/reset register    */

            struct
            {
                __IOM uint32_t BS0 : 1;  /*!< [0..0] BS0   */
                __IOM uint32_t BS1 : 1;  /*!< [1..1] BS1   */
                __IOM uint32_t BS2 : 1;  /*!< [2..2] BS2   */
                __IOM uint32_t BS3 : 1;  /*!< [3..3] BS3   */
                __IOM uint32_t BS4 : 1;  /*!< [4..4] BS4   */
                __IOM uint32_t BS5 : 1;  /*!< [5..5] BS5   */
                __IOM uint32_t BS6 : 1;  /*!< [6..6] BS6   */
                __IOM uint32_t BS7 : 1;  /*!< [7..7] BS7   */
                __IOM uint32_t BS8 : 1;  /*!< [8..8] BS8   */
                __IOM uint32_t BS9 : 1;  /*!< [9..9] BS9   */
                __IOM uint32_t BS10 : 1; /*!< [10..10] BS10*/
                __IOM uint32_t BS11 : 1; /*!< [11..11] BS11*/
                __IOM uint32_t BS12 : 1; /*!< [12..12] BS12*/
                __IOM uint32_t BS13 : 1; /*!< [13..13] BS13*/
                __IOM uint32_t BS14 : 1; /*!< [14..14] BS14*/
                __IOM uint32_t BS15 : 1; /*!< [15..15] BS15*/
                __IOM uint32_t BR0 : 1;  /*!< [16..16] BR0 */
                __IOM uint32_t BR1 : 1;  /*!< [17..17] BR1 */
                __IOM uint32_t BR2 : 1;  /*!< [18..18] BR2 */
                __IOM uint32_t BR3 : 1;  /*!< [19..19] BR3 */
                __IOM uint32_t BR4 : 1;  /*!< [20..20] BR4 */
                __IOM uint32_t BR5 : 1;  /*!< [21..21] BR5 */
                __IOM uint32_t BR6 : 1;  /*!< [22..22] BR6 */
                __IOM uint32_t BR7 : 1;  /*!< [23..23] BR7 */
                __IOM uint32_t BR8 : 1;  /*!< [24..24] BR8 */
                __IOM uint32_t BR9 : 1;  /*!< [25..25] BR9 */
                __IOM uint32_t BR10 : 1; /*!< [26..26] BR10*/
                __IOM uint32_t BR11 : 1; /*!< [27..27] BR11*/
                __IOM uint32_t BR12 : 1; /*!< [28..28] BR12*/
                __IOM uint32_t BR13 : 1; /*!< [29..29] BR13*/
                __IOM uint32_t BR14 : 1; /*!< [30..30] BR14*/
                __IOM uint32_t BR15 : 1; /*!< [31..31] BR15*/
            } CS_BSRR_b;
        };

        union
        {
            __IM uint32_t CS; /*!< (@ 0x00000034) return GPIO port cmos/schmitt when read   */

            struct
            {
                __IM uint32_t CS0 : 1;  /*!< [0..0] CS0   */
                __IM uint32_t CS1 : 1;  /*!< [1..1] CS1   */
                __IM uint32_t CS2 : 1;  /*!< [2..2] CS2   */
                __IM uint32_t CS3 : 1;  /*!< [3..3] CS3   */
                __IM uint32_t CS4 : 1;  /*!< [4..4] CS4   */
                __IM uint32_t CS5 : 1;  /*!< [5..5] CS5   */
                __IM uint32_t CS6 : 1;  /*!< [6..6] CS6   */
                __IM uint32_t CS7 : 1;  /*!< [7..7] CS7   */
                __IM uint32_t CS8 : 1;  /*!< [8..8] CS8   */
                __IM uint32_t CS9 : 1;  /*!< [9..9] CS9   */
                __IM uint32_t CS10 : 1; /*!< [10..10] CS10*/
                __IM uint32_t CS11 : 1; /*!< [11..11] CS11*/
                __IM uint32_t CS12 : 1; /*!< [12..12] CS12*/
                __IM uint32_t CS13 : 1; /*!< [13..13] CS13*/
                __IM uint32_t CS14 : 1; /*!< [14..14] CS14*/
                __IM uint32_t CS15 : 1; /*!< [15..15] CS15*/
            } CS_b;
        };
    };

    union
    {
        union
        {
            __IOM uint32_t OS_BSRR; /*!< (@ 0x00000038) GPIO port open source bit set/reset register*/

            struct
            {
                __IOM uint32_t BS0 : 1;  /*!< [0..0] BS0   */
                __IOM uint32_t BS1 : 1;  /*!< [1..1] BS1   */
                __IOM uint32_t BS2 : 1;  /*!< [2..2] BS2   */
                __IOM uint32_t BS3 : 1;  /*!< [3..3] BS3   */
                __IOM uint32_t BS4 : 1;  /*!< [4..4] BS4   */
                __IOM uint32_t BS5 : 1;  /*!< [5..5] BS5   */
                __IOM uint32_t BS6 : 1;  /*!< [6..6] BS6   */
                __IOM uint32_t BS7 : 1;  /*!< [7..7] BS7   */
                __IOM uint32_t BS8 : 1;  /*!< [8..8] BS8   */
                __IOM uint32_t BS9 : 1;  /*!< [9..9] BS9   */
                __IOM uint32_t BS10 : 1; /*!< [10..10] BS10*/
                __IOM uint32_t BS11 : 1; /*!< [11..11] BS11*/
                __IOM uint32_t BS12 : 1; /*!< [12..12] BS12*/
                __IOM uint32_t BS13 : 1; /*!< [13..13] BS13*/
                __IOM uint32_t BS14 : 1; /*!< [14..14] BS14*/
                __IOM uint32_t BS15 : 1; /*!< [15..15] BS15*/
                __IOM uint32_t BR0 : 1;  /*!< [16..16] BR0 */
                __IOM uint32_t BR1 : 1;  /*!< [17..17] BR1 */
                __IOM uint32_t BR2 : 1;  /*!< [18..18] BR2 */
                __IOM uint32_t BR3 : 1;  /*!< [19..19] BR3 */
                __IOM uint32_t BR4 : 1;  /*!< [20..20] BR4 */
                __IOM uint32_t BR5 : 1;  /*!< [21..21] BR5 */
                __IOM uint32_t BR6 : 1;  /*!< [22..22] BR6 */
                __IOM uint32_t BR7 : 1;  /*!< [23..23] BR7 */
                __IOM uint32_t BR8 : 1;  /*!< [24..24] BR8 */
                __IOM uint32_t BR9 : 1;  /*!< [25..25] BR9 */
                __IOM uint32_t BR10 : 1; /*!< [26..26] BR10*/
                __IOM uint32_t BR11 : 1; /*!< [27..27] BR11*/
                __IOM uint32_t BR12 : 1; /*!< [28..28] BR12*/
                __IOM uint32_t BR13 : 1; /*!< [29..29] BR13*/
                __IOM uint32_t BR14 : 1; /*!< [30..30] BR14*/
                __IOM uint32_t BR15 : 1; /*!< [31..31] BR15*/
            } OS_BSRR_b;
        };

        union
        {
            __IM uint32_t OS; /*!< (@ 0x00000038) return GPIO port open source when read    */

            struct
            {
                __IM uint32_t OS0 : 1;  /*!< [0..0] OS0   */
                __IM uint32_t OS1 : 1;  /*!< [1..1] OS1   */
                __IM uint32_t OS2 : 1;  /*!< [2..2] OS2   */
                __IM uint32_t OS3 : 1;  /*!< [3..3] OS3   */
                __IM uint32_t OS4 : 1;  /*!< [4..4] OS4   */
                __IM uint32_t OS5 : 1;  /*!< [5..5] OS5   */
                __IM uint32_t OS6 : 1;  /*!< [6..6] OS6   */
                __IM uint32_t OS7 : 1;  /*!< [7..7] OS7   */
                __IM uint32_t OS8 : 1;  /*!< [8..8] OS8   */
                __IM uint32_t OS9 : 1;  /*!< [9..9] OS9   */
                __IM uint32_t OS10 : 1; /*!< [10..10] OS10*/
                __IM uint32_t OS11 : 1; /*!< [11..11] OS11*/
                __IM uint32_t OS12 : 1; /*!< [12..12] OS12*/
                __IM uint32_t OS13 : 1; /*!< [13..13] OS13*/
                __IM uint32_t OS14 : 1; /*!< [14..14] OS14*/
                __IM uint32_t OS15 : 1; /*!< [15..15] OS15*/
            } OS_b;
        };
    };
} GPIOF_Type; /*!< Size = 60 (0x3c)    */

// 测试在结构体中内嵌枚举
typedef struct {
    int id;
    enum {
        STATUS_ACTIVE = 1,
        STATUS_INACTIVE = 0
    } status;
    char name[50];
} UserWithEmbeddedEnum;

// 测试在联合体中内嵌枚举
typedef union {
    int value;
    enum {
        TYPE_INTEGER = 0,
        TYPE_FLOAT = 1
    } type;
} DataWithEmbeddedEnum;

#endif // EMBEDDED_ENUM_TEST_H
