#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <stdbool.h>

typedef enum { VAR, ABS, APP } ExprType;

typedef struct Expr {
    ExprType type;
    union {
        char var;
        struct { char param; struct Expr* body; } abs;
        struct { struct Expr* left; struct Expr* right; } app;
    };
} Expr;

const char* input;
int pos = 0;

#define MAX_REDUCE_DEPTH 1000

void skip_whitespace() { while (isspace(input[pos])) pos++; }
int is_lambda(const char* s) { return (unsigned char)s[0] == 0xCE && (unsigned char)s[1] == 0xBB; }
Expr* parse_expr();
Expr* parse_simple_expr();
Expr* parse_abs();
Expr* parse_var();
Expr* parse_paren();
Expr* copy_expr(Expr* e);
void free_expr(Expr* e);
bool expr_equal(Expr* a, Expr* b);
bool is_free_var(Expr* e, char var);
Expr* alpha_rename(Expr* e, char old_var, char new_var);
bool is_redex(Expr* e) { return e && e->type == APP && e->app.left && e->app.left->type == ABS; }
Expr* substitute(Expr* body, char var, Expr* val);
Expr* beta_reduce_one_step(Expr* e);
Expr* beta_reduce_full(Expr* e);
void print_expr_internal(Expr* e, bool needs_parens);
void print_expr(Expr* e) { print_expr_internal(e, false); }
void run_tests();

int main() {
    run_tests();
    return 0;
}

Expr* parse_var() {
    Expr* e = malloc(sizeof(Expr));
    e->type = VAR;
    e->var = input[pos++];
    return e;
}

Expr* parse_paren() {
    pos++;
    Expr* e = parse_expr();
    pos++;
    return e;
}

Expr* parse_simple_expr() {
    skip_whitespace();
    if (is_lambda(&input[pos])) return parse_abs();
    if (input[pos] == '(') return parse_paren();
    return parse_var();
}

Expr* parse_abs() {
    pos += 2;
    char param = input[pos++];
    pos++;
    Expr* body = parse_expr();
    Expr* e = malloc(sizeof(Expr));
    e->type = ABS;
    e->abs.param = param;
    e->abs.body = body;
    return e;
}

Expr* parse_expr() {
    Expr* left = parse_simple_expr();
    skip_whitespace();
    while (input[pos] && input[pos] != ')' && input[pos] != '.') {
        Expr* right = parse_simple_expr();
        Expr* app = malloc(sizeof(Expr));
        app->type = APP;
        app->app.left = left;
        app->app.right = right;
        left = app;
        skip_whitespace();
    }
    return left;
}

Expr* copy_expr(Expr* e) {
    if (!e) return NULL;
    Expr* c = malloc(sizeof(Expr));
    c->type = e->type;
    if (e->type == VAR) {
        c->var = e->var;
    } else if (e->type == ABS) {
        c->abs.param = e->abs.param;
        c->abs.body = copy_expr(e->abs.body);
    } else if (e->type == APP) {
        c->app.left = copy_expr(e->app.left);
        c->app.right = copy_expr(e->app.right);
    }
    return c;
}

void free_expr(Expr* e) {
    if (!e) return;
    if (e->type == ABS) free_expr(e->abs.body);
    else if (e->type == APP) {
        free_expr(e->app.left);
        free_expr(e->app.right);
    }
    free(e);
}

bool expr_equal(Expr* a, Expr* b) {
    if (a == b) return true;
    if (!a || !b) return false;
    if (a->type != b->type) return false;
    switch (a->type) {
        case VAR: return a->var == b->var;
        case ABS: return a->abs.param == b->abs.param && expr_equal(a->abs.body, b->abs.body);
        case APP: return expr_equal(a->app.left, b->app.left) && expr_equal(a->app.right, b->app.right);
    }
    return false;
}

bool is_free_var(Expr* e, char var) {
    if (!e) return false;
    if (e->type == VAR) return e->var == var;
    if (e->type == ABS) return e->abs.param != var && is_free_var(e->abs.body, var);
    if (e->type == APP) return is_free_var(e->app.left, var) || is_free_var(e->app.right, var);
    return false;
}

Expr* alpha_rename(Expr* e, char old_var, char new_var) {
    if (!e) return NULL;
    Expr* c = malloc(sizeof(Expr));
    c->type = e->type;
    if (e->type == VAR) {
        c->var = e->var == old_var ? new_var : e->var;
    } else if (e->type == ABS) {
        c->abs.param = e->abs.param == old_var ? new_var : e->abs.param;
        c->abs.body = alpha_rename(e->abs.body, old_var, new_var);
    } else if (e->type == APP) {
        c->app.left = alpha_rename(e->app.left, old_var, new_var);
        c->app.right = alpha_rename(e->app.right, old_var, new_var);
    }
    return c;
}

Expr* substitute(Expr* body, char var, Expr* val) {
    if (!body) return NULL;
    
    if (body->type == VAR) {
        return body->var == var ? copy_expr(val) : copy_expr(body);
    }
    else if (body->type == ABS) {
        if (body->abs.param == var) {
            return copy_expr(body);
        }
        
        if (is_free_var(val, body->abs.param)) {
            char new_var = 'a';
            while (new_var <= 'z' && 
                   (is_free_var(body, new_var) || is_free_var(val, new_var))) {
                ++new_var;
            }
            if (new_var > 'z') {
                return copy_expr(body);
            }
            
            Expr* renamed_body = alpha_rename(body->abs.body, body->abs.param, new_var);
            Expr* new_abs = malloc(sizeof(Expr));
            new_abs->type = ABS;
            new_abs->abs.param = new_var;
            new_abs->abs.body = substitute(renamed_body, var, val);
            free_expr(renamed_body);
            return new_abs;
        }
        else {
            Expr* new_body = substitute(body->abs.body, var, val);
            Expr* new_abs = malloc(sizeof(Expr));
            new_abs->type = ABS;
            new_abs->abs.param = body->abs.param;
            new_abs->abs.body = new_body;
            return new_abs;
        }
    }
    else if (body->type == APP) {
        Expr* new_left = substitute(body->app.left, var, val);
        Expr* new_right = substitute(body->app.right, var, val);
        Expr* new_app = malloc(sizeof(Expr));
        new_app->type = APP;
        new_app->app.left = new_left;
        new_app->app.right = new_right;
        return new_app;
    }
    return NULL;
}

Expr* beta_reduce_one_step(Expr* e) {
    if (!e) return NULL;
    
    if (is_redex(e)) {
        return substitute(e->app.left->abs.body, e->app.left->abs.param, e->app.right);
    }
    else if (e->type == ABS) {
        Expr* new_body = beta_reduce_one_step(e->abs.body);
        if (new_body != e->abs.body) {
            Expr* new_abs = malloc(sizeof(Expr));
            new_abs->type = ABS;
            new_abs->abs.param = e->abs.param;
            new_abs->abs.body = new_body;
            return new_abs;
        }
    }
    else if (e->type == APP) {
        Expr* new_left = beta_reduce_one_step(e->app.left);
        if (new_left != e->app.left) {
            Expr* new_app = malloc(sizeof(Expr));
            new_app->type = APP;
            new_app->app.left = new_left;
            new_app->app.right = copy_expr(e->app.right);
            return new_app;
        }
        
        Expr* new_right = beta_reduce_one_step(e->app.right);
        if (new_right != e->app.right) {
            Expr* new_app = malloc(sizeof(Expr));
            new_app->type = APP;
            new_app->app.left = copy_expr(e->app.left);
            new_app->app.right = new_right;
            return new_app;
        }
    }
    
    return copy_expr(e);
}

Expr* beta_reduce_full(Expr* e) {
    Expr* current = copy_expr(e);
    int steps = 0;
    while (steps < MAX_REDUCE_DEPTH) {
        Expr* next = beta_reduce_one_step(current);
        if (expr_equal(current, next)) {
            free_expr(next);
            return current;
        }
        free_expr(current);
        current = next;
        ++steps;
    }
    printf("Warning: reached maximum reduction depth\n");
    return current;
}

void print_expr_internal(Expr* e, bool needs_parens) {
    if (!e) return;
    
    if (e->type == VAR) {
        printf("%c", e->var);
    } 
    else if (e->type == ABS) {
        if (needs_parens) printf("(");
        printf("λ%c.", e->abs.param);
        print_expr_internal(e->abs.body, false);
        if (needs_parens) printf(")");
    } 
    else if (e->type == APP) {
        if (needs_parens) printf("(");
        print_expr_internal(e->app.left, e->app.left->type == APP);
        printf(" ");
        print_expr_internal(e->app.right, e->app.right->type == APP || e->app.right->type == ABS);
        if (needs_parens) printf(")");
    }
}

void run_tests() {
    const char* tests[] = {
        "(λx.x) y",
        "(λx.λy.x) a b",
        "(λx.x x) (λx.x x)",
        "λx.x",
        "(λx.λy.x y) a b",
        "(λx.λy.x) (λz.z) a",
        "((λx.x) (λy.y))",
        "(λx. x (λy.y)) z",
        "(λx.λy.x y) (λz.z) a",
        "((λx.λy.x) a) b"
    };

    for (int i = 0; i < sizeof(tests)/sizeof(tests[0]); ++i) {
        printf("Test %d: %s\n", i+1, tests[i]);
        input = tests[i];
        pos = 0;
        Expr* expr = parse_expr();
        Expr* reduced = beta_reduce_full(expr);
        printf("After β-red: ");
        print_expr(reduced);
        printf("\n\n");
        free_expr(expr);
        free_expr(reduced);
    }
}
