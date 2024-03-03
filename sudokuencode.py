import sys, os, math

def sudoku_from_file():
    args = sys.argv
    if len(args) != 2:
        sys.exit(f"usage: python3 ./{args[0]} input_sudoku_file.txt")
        
    
    try:
        with open(args[1], "r") as f:
            sudoku_in = []
            for line in f.readlines():
                #converto le stringhe in interi
                int_line = list(map(lambda t: int(t), line.replace('/n','').split()))
                sudoku_in.append(int_line)
            return sudoku_in
    except Exception as e:
        sys.exit(e)

def num_to_cnf(cnf_var, num, invert):
    """
    converto i numeri in clausole cnf
    le variabili cnf sono 1 2 3 4
    se, ad esempio, converto 5 in binario (0 1 0 1), avrò la clausola:
    -1 2 -3 4 (lo 0 corrisponde ad una negazione in cnf)
    se invert = true, inverto 0 e 1
    """
    s = -1 if invert else 1
    #stesso numero di cifre binarie, stesso numero di variabili cnf
    bin_list = map(lambda t: int(t), bin(num)[2:].zfill(len(cnf_var)))
    new_clause = [*map(lambda t: s*t[0] if t[1] else -s*t[0], zip(cnf_var, bin_list))]
    return new_clause

#vincoli: p e q devono essere diversi
def print_different_num_cnf(fp, p, q, n):
    for num in range(1, n+1):
        for p1 in num_to_cnf(p, num, True):
            fp.write(f"{p1} ")
        for q1 in num_to_cnf(q, num, True):
            fp.write(f"{q1} ")
        fp.write("0\n")

def insert(originalfile, string):
    with open(originalfile, 'r') as f:
        with open('newfile.txt', 'w') as f2:
            f2.write(string + '\n')
            f2.write(f.read())
    os.rename('newfile.txt', originalfile)
    
def make_cnf_dimacs(sudoku_in, out_file):
    clauses_number = 0
    #dimensione del puzzle e numero minimo di bit per rappresentare un numero
    n = len(sudoku_in[0])
    block = int(math.sqrt(n))
    num_of_bits = len(bin(n)[2:])
    
    with open(out_file, 'w') as f:
        for i in range (1, n*n+1):
            p = [num_of_bits*i - (num_of_bits-1) + offset for offset in range(num_of_bits)]
            
            #VINCOLI: numeri validi nel sudoku vanno da 1 a n
            forbidden_numbers = [*range(n+1, 1 << num_of_bits)]
            forbidden_numbers.append(0)
            for num in forbidden_numbers:
                for j in num_to_cnf(p, num, True):
                    f.write(f"{j} ")
                clauses_number += 1
                f.write("0\n")
                
            #VINCOLI: aggiungo i numeri dati nel puzzle in input
            #converto il numero seriale (1-n*n) in indici (i,j)
            curr_num = sudoku_in[(i-1)//n][(i-1)%n]
            if curr_num != 0:
                for j in num_to_cnf(p, curr_num, False):
                    f.write(f"{j} 0\n")
                    clauses_number +=1
            
            #VINCOLI: in ogni riga, ogni colonna, ed ogni sottogriglia numeri diversi da 1 a 9
            for j in range(i+1, n*n+1):
                q = [num_of_bits*j - (num_of_bits-1) + offset for offset in range(num_of_bits)]
                
                #righe
                if(i-1)//n == (j-1)//n:
                    print_different_num_cnf(f, p, q, n)
                    clauses_number += n
                
                #colnne
                elif(i-1)%n == (j-1)%n:
                    print_different_num_cnf(f, p, q, n)
                    clauses_number += n
                
                #sottogriglie
                elif(((i-1)//n)//block, ((i-1)%n)//block) == (((j-1)//n)//block, ((j-1)%n)//block):
                    print_different_num_cnf(f, p, q, n)
                    clauses_number += n
    
    insert(out_file, f"p cnf {n*n*num_of_bits} {clauses_number}")
    return n

def ksplit(line, sep, k):
    '''
    Splitta le stringhe per ogni k occorrenze di sep
    '''
    line = line.split(sep)
    return [line[i:i+k] for i in range(0, len(line), k)]
            
def cnf_to_num(cnf_clause):
    '''
    Funzione inversa di num_to_cnf
    converte una clausola in un numero
    '''
    str_bin = [*map(lambda digit: '1' if int(digit) > 0 else '0', cnf_clause)]
    return int(''.join(str_bin), 2)

def decode_output(sat_output, n):
    num_of_bits = len(bin(n)[2:])
    
    with open(sat_output, 'r') as f:
        solution = f.read()
        if solution[:3] != 'SAT':
            sys.exit(0)
            
    
    solution = solution.replace(' 0\n', '').replace('SAT\n', '')
    
    #decodifico e scrivo la matrice risolta
    out_sudoku = "out_sudoku.txt"
    with open(out_sudoku, "w") as g:
        for i, cnf_num in enumerate(ksplit(solution, ' ', num_of_bits)):
            num = cnf_to_num(cnf_num)
            g.write(f"{num} ")
            if (i+1) % n == 0:
                g.write("\n")
                

def main():
    sudoku_in = sudoku_from_file()
    out_file = "out_sudoku.cnf"
    
    n = make_cnf_dimacs(sudoku_in, out_file)
    
    #risolvo sudoku con minisat
    sat_output = 'sat_sudoku_solution.txt'
    os.system(f"minisat -verb=2 {out_file} {sat_output}")
    
    #Decodifico e stampo a file
    decode_output(sat_output, n)
    
if __name__ == "__main__":
    main()