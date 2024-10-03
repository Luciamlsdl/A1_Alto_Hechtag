import os
import threading
from concurrent.futures import ThreadPoolExecutor
import time
import random
import subprocess
import hashlib
import base58

# Definição dos parâmetros de range e número de threads
min_range = 0x8000000000000000000000000000000000000000
max_range = 0xffffffffffffffffffffffffffffffffffffffff
num_threads = 4  # Número de threads paralelas
wallets = ['138XxHZGcKM6WyWuYCijLsoCd8K3x4WYjs']  # Substitua pela sua carteira alvo

start_time = time.time()

# Função para desligar a internet
def desligar_internet():
    try:
        print("Desligando a internet para garantir segurança...")
        if os.name == 'nt':  # Se for Windows
            subprocess.run("netsh interface set interface 'Wi-Fi' admin=disable", shell=True)
        else:  # Se for Linux ou MacOS
            subprocess.run("nmcli networking off", shell=True)
        print("Internet desligada.")
    except Exception as e:
        print(f"Erro ao tentar desligar a internet: {e}")

# Função para gerar a chave privada BTC (hexadecimal aleatória)
def gerar_chave_privada_btc():
    chave_privada = hex(random.randint(min_range, max_range))[2:]  # Gera a chave e remove o '0x'
    print(f"Chave privada BTC gerada: {chave_privada}")
    return chave_privada

# Função para converter chave privada para WIF (Wallet Import Format)
def chave_privada_para_wif(chave_privada_hex):
    prefix = b'\x80'  # Prefixo para chave privada Bitcoin mainnet
    chave_privada_bytes = bytes.fromhex(chave_privada_hex)
    extended_key = prefix + chave_privada_bytes

    # Primeiro hash SHA-256
    sha256_1 = hashlib.sha256(extended_key).digest()

    # Segundo hash SHA-256
    sha256_2 = hashlib.sha256(sha256_1).digest()

    # Adiciona os 4 primeiros bytes do segundo hash ao final da extended key
    chave_com_checksum = extended_key + sha256_2[:4]

    # Converte para base58 (formato WIF)
    wif = base58.b58encode(chave_com_checksum)
    return wif.decode()

# Função para enviar os fundos para a sua carteira Electrum
def enviar_fundos_electrum(chave_wif):
    try:
        # Substitua 'sua_carteira_recebimento' pelo endereço de recebimento na sua Electrum
        carteira_recebimento = 'sua_carteira_recebimento'
        
        # Cria e assina a transação usando a chave privada WIF no Electrum via CLI
        comando = f"electrum payto {carteira_recebimento} 0.001 --privkey={chave_wif} --broadcast"
        subprocess.run(comando, shell=True, check=True)
        print(f"Transação enviada com sucesso usando a chave WIF: {chave_wif}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao enviar a transação: {e}")

# Função que será executada por cada thread
def tarefa_worker(start, end):
    print(f"Thread trabalhando no intervalo: {hex(start)} - {hex(end)}")
    while True:  # Loop infinito até que seja interrompido manualmente
        chave_privada = gerar_chave_privada_btc()
        if chave_privada in wallets:
            print(f"Chave encontrada para a carteira {wallets}: {chave_privada}")
            chave_wif = chave_privada_para_wif(chave_privada)
            enviar_fundos_electrum(chave_wif)
            break

# Função principal para distribuir a carga entre os workers
def main():
    range_por_thread = (max_range - min_range) // num_threads
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(num_threads):
            start = min_range + i * range_por_thread
            end = max_range if i == num_threads - 1 else start + range_por_thread - 1
            futures.append(executor.submit(tarefa_worker, start, end))

        for future in futures:
            future.result()

    print("Todos os workers concluíram com sucesso.")
    print('Tempo de execução:', round(time.time() - start_time, 2), 'segundos')

# Desligar a internet antes de prosseguir
desligar_internet()

# Executar o código principal
main()
