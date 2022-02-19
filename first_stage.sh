#!/bin/bash
for fir in 15
do
    sec=0
    while [ "$sec" -lt 8 ]
    do
        echo "running fir ${fir} sec ${sec}"
        python3 main.py --first_stage ${fir} --second_stage ${sec} --n_steps 170
        sec=$(( sec + 1 ))
    done
done
