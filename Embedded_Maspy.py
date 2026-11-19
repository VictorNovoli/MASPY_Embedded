from typing import Iterable
import javino
from maspy import *
from maspy.agent import Belief, Goal
import re, threading, time

PERCEPT_RE = re.compile(r"(\w+)\(([^)]*)\)")

def parse_percepts(raw: str):
    """'lightSensor(756);lighthouse(0)' -> [('lightSensor', 756), ('lighthouse', 0)]"""
    out = []
    for name, arg in PERCEPT_RE.findall(raw):
        try:    val = int(arg)
        except ValueError:
            try:    val = float(arg)
            except ValueError: val = arg
        out.append((name, val))
    return out

class Genneric_environment(Environment): 
    def __init__(self, env_name, ser):
        self.ser = ser
        super().__init__(env_name)
        self.perguntar(ser)
        #função responsável por pegar os percepts da porta serial
    
    def perguntar(self, ser): #ser é o objeto da conexão serial
        javino.sendMsg(ser, "getPercepts") #envia pra porta serial a mensagem getPercepts
        for _ in range(100):               # ~2 segundos de tentativa
            if javino.availableMsg(ser): #verifica se existem bytes disponíveis na porta serial
                percept = javino.getMsg()
                for nome, valor in parse_percepts(percept):
                     self.create(Percept(nome, (valor,)))
                break # CORREÇÃO: sai do laço depois de ler a resposta (antes continuava tentando até 100 vezes)

    def update_environment(self, led):
        if led == "ledStatus(off)":
            javino.sendMsg(self.ser, "ledOn")
            self.print("Sending a message to the serial port - Turn on")
            time.sleep(0.9)        
            helper1 = self.get(Percept("ledStatus", ("off"))) #armazena o percept antigo - led = off -
            if helper1:
                self.delete(helper1) #deleta o percept antigo de que estava desligado
                self.create(Percept("ledStatus", ("on",))) #novo percept de que o led esta ligadp
                self.print("New percept -Led on - created")
                time.sleep(0.9)       

        if led == "ledStatus(on)":
            javino.sendMsg(self.ser, "ledOff")
            self.print("Sending a message to the serial port - Turn off")
            time.sleep(0.9)       
            helper1 = self.get(Percept("ledStatus", ("on"))) #armazena o percept antigo - led = off -
            if helper1:
                self.delete(helper1) #deleta o percept antigo de que estava desligado
                self.create(Percept("ledStatus", ("off",))) #novo percept de que o led esta ligadp
                self.print("New percept -Led off - created")
                time.sleep(0.9)       
    



class Basic_Agent(Agent):
    def __init__(self, agt_name=None):
        super().__init__(agt_name)
        self.rodando = False #variável usada como condição de parada pro loop 
        self.lock = threading.Lock() #conferir se é aqui mesmo que eu coloco 
        self.add(Goal("analyze_environment"))

    def start_loop(self): #conferir se eu passo só self mesmo
        self.rodando = True
        thread_loop = threading.Thread(target= self.perceivenv, daemon= True) #aqui eu crio a thread com a função alvo
        thread_loop.start()


    def stop_loop(self): #função que deve ser chamada na main pra que a condição do perceiven fique falsa e o loop pare 
        self.rodando = False


    def perceivenv(self, src): #função que o agente roda em loop para estar sempre percebendo o ambiente
        while self.rodando:
            with self.lock:
                # execução do código aqui


    @pl(gain, Goal("analyze_environment"))
    def read_environment(self, src):
        led = self.get(Belief("ledStatus", Any, "Env"))
        if led:
            print("Sucess reading the Environment")
            time.sleep(0.9)       
            print(f"Belief: {led}")
            time.sleep(0.9)       
            valor = led.values[0] if isinstance(led.values, tuple) else led.values #descobre o texto que está dentro do Belief
            env.update_environment(f"ledStatus({valor})")  # CORREÇÃO: o método recebe só 1 argumento
        else:
            print("No Percept on the Environment")
            time.sleep(0.9)       

        


#Num Raspberry Pi real, um pino configurado como saída começa em nível baixo (LOW), a menos que você passe um valor inicial.
#O estado inicial vem da configuração do pino (.setup)
#GPIO.setup(PIN_LED, GPIO.OUT)   # configura o pino 18 como SAÍDA (ele vai comandar o LED)
#GPIO.output(PIN_LED, HIGH)      # ESCREVE: manda tensão para o pino (LED acende)
#GPIO.input(PIN_LED)             # LÊ: pergunta qual nível está no pino agora

#no RPi.GPIO, output significa escrever no pino e input significa ler o pino.

#Explanation of some javino functions bellow:
#javino.start(porta)	Abre a porta serial e devolve um identificador da conexão (comm). Todas as outras funções usam esse comm para saber de qual conexão falar. Retorna falso se não conseguir abrir.
#javino.availableMsg(comm)	Pergunta: “chegou uma mensagem completa e válida?”. Não bloqueia, só responde sim ou não.
#javino.getMsg(comm)	Entrega o texto dessa mensagem (por exemplo, "getPercepts").
#javino.addPercept(texto)	Coloca um percept num buffer de saída. Ainda não envia.
#javino.sendPercepts(comm)	Envia o buffer inteiro de uma vez como uma só mensagem e o esvazia.

if __name__ == "__main__":
    porta = "/tmp/ttyEmulatedPort0" #como passar essa porta pro ambiente?
    ser = javino.start(porta)  
    env = Genneric_environment("Env", ser)
    agent = Basic_Agent("agent1")
    env._add_agent(agent)
    Admin().connect_to(agent, env)
    Admin().start_system()
    
