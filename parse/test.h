#ifndef what

#define ITWORKS 1

    #ifndef HUH

    #define NESTED 1

        #ifndef AGAIN

        #define INCEPTION 1
        #define A 5
        #define B (2 * A + INCEPTION)
        #define C (LMAO)

        #ifdef meh
        #endif

        #endif

    #endif

#define AFTER 1

#endif

#if defined(A) && defined(B) && defined(D)
    #error hey
#endif