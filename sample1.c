#include <stdio.h>
int main(void){
    int a[5] = {1, 2, 3, 4, 5};
    int b[5];
{%box(②,15,3,-1)%}
    for  (int i=0; i<5; i++){
        printf("%d",b[i]);
    }
    return 0;
}
