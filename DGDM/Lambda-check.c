#include <stdio.h>
#include <stdbool.h>
#include <ctype.h>
#include <string.h>

bool parse_expression(const char **ptr);
bool parse_abstraction(const char **ptr);

bool is_valid_lambda_expression(const char *str);
bool is_lambda(const char *c) { return c[0] == '\xCE' && c[1] == '\xBB'; }
bool is_valid_variable(const char c) { return isalpha(c); }

void test_lambda(const char *str);

int main() {
    const char* lambda_tests[] = {
        "λx.x",
        "λx.y",
        "λx.xy",
        "λx.xyz",
        "λx.λy.x",
        "λxy.x",
        "λxyz.xz(yz)",

        "(λx.x)",
        "λx.(x y)",
        "λx.(λy.x)",
        "(λx.x)y",
        "(λx.xy)(λy.yz)",
        "λx.(y (z x))",
        
        "x y z",
        "λx.x y z",
        "λf.λx.f (f x)",
        "(λx.x x)(λx.x x)",
        "λx.(λy.(x y)) z",
        
        "λf.(λx.f (x x))(λx.f (x x))",
        "λab.a",
        "λab.b",
        "λabc.ac(bc)",
        "λab.bab",
        
        "λx..y",
        "x.λy",
        "λx.(y",
        "λ1.1",
        "λx.λy.",
        "λx.(y))",
        "λx x.x",
        "λx.(y z",
        "λx..",
        "",
        ".",
        "λ.",
        "x y. z",
        "λx.(y z))",
        "λx.()",
        "λx.(λy.)",
        
        "(λsz.z)(λsz.s(sz))",
        "λmnfx.mf(nfx)",
        "λnfx.f(nfx)",
        "λfx.x",
        "λfx.fx",
        "λfx.f(fx)",

        "λx.λy.λz.z y x",
        "λx.(λy.y)(λz.z)",
        "λ_.λ_._",
        "λx.λx.x",
        "λa.a(λb.b)b",
        
        "(λx.λy.λz.x y z)(λa.a)(λb.b)(λc.c)",
        "λf.(λx.f(λy.x x y))(λx.f(λy.x x y))",
        "(λxyz.xz(yz))(λab.a)(λcd.c)",
        "λx.(λy.(λz.(x y) z))",
        "(λx.x x)(λy.y y y)"
    };
    const size_t num_tests = sizeof(lambda_tests) / sizeof(lambda_tests[0]);
    printf("Lambda-expressions:\n");
    for (size_t i = 0; i < num_tests; ++i) {
        test_lambda(lambda_tests[i]);
    }
    
    return 0;
}

bool parse_expression(const char **ptr) {
    const char *p = *ptr;
    
    if (*p == '(') {
        ++p;
        if (!parse_expression(&p)) return false;
        if (*p != ')') return false;
        ++p;
    } 
    else if (is_lambda(p)) {
        if (!parse_abstraction(&p)) return false;
    }
    else {
        if (!is_valid_variable(*p)) return false;
        ++p;
    }

    while (*p == ' ') ++p;
    
    while (true) {
        const char *q = p;
        while (*p == ' ') ++p;

        if (*q == '(') {
            ++q;
            if (!parse_expression(&q)) break;
            if (*q != ')') break;
            ++q;
        } 
        else if (is_lambda(q)) break;
        else if (is_valid_variable(*q)) ++q;
        else break;

        p = q;
    }
    
    *ptr = p;
    return true;
}

bool parse_abstraction(const char **ptr) {
    const char *p = *ptr;
    
    if (!is_lambda(p)) return false;
    p += 2;
    
    if (!is_valid_variable(*p)) return false;
    ++p;

    if (*p != '.') return false;
    ++p;
    
    if (!parse_expression(&p)) return false;
    
    *ptr = p;
    return true;
}

bool is_valid_lambda_expression(const char *str) {
    const char *p = str;
    if (!parse_expression(&p)) return false;
    return *p == '\0';
}

void test_lambda(const char *str) {
    printf("%-7s: %.*s\n",
        is_valid_lambda_expression(str) ? "OK" : "NOT OK",
        (int)strcspn(str, "\n"), str);
}