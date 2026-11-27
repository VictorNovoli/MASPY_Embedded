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
        time.sleep(2)
        super().__init__(env_name)
        self.perguntar(ser)
        #função responsável por pegar os percepts da porta serial
    
    def perguntar(self, ser): #ser é o objeto da conexão serial
        javino.sendMsg(ser, "getPercepts") #envia pra porta serial a mensagem getPercepts
        for _ in range(100):               # ~2 segundos de tentativa
            if javino.availableMsg(ser): #verifica se existem bytes disponíveis na porta serial
                percept = javino.getMsg()
                print("RAW:", repr(percept), type(percept))   
                for nome, valor in parse_percepts(percept):
                     if valor == "off":
                         self.create(Percept("ledStatus", ("off",)))
                         antigo1 = self.get(Percept("ledStatus", ("on",)))
                         if antigo1:
                            self.delete(antigo1)
                     else:
                         self.create(Percept("ledStatus", ("on",)))
                         antigo = self.get(Percept("ledStatus", ("off",)))   # pega o percept guardado no ambiente
                         if antigo:
                           self.delete(antigo)          
                     break                    # apaga esse objeto
                     #self.create(Percept(nome, (valor,)))
            else:
                self.print("No answer from the serial port yet")    
            #break # CORREÇÃO: sai do laço depois de ler a resposta (antes continuava tentando até 100 vezes)
            time.sleep(0.02)   # 100 x 20 ms = ~2 s
        #else:
            #print("perguntar: sem resposta da serial")
    
    def chamar_perguntar(self, agt):
        self.perguntar(self.ser)
        
    def led_on(self, agt): # ação do ambiente: só executa o que o agente decidiu (agt: nome do agente, passado pelo MASPY)
        javino.sendMsg(self.ser, "ledOn")
        self.print("Sending a message to the serial port - Turn on")
        time.sleep(0.9)        
        self.perguntar(self.ser) # lê o novo estado na porta serial: o percept só muda se o Arduino confirmar
        time.sleep(0.9)       

    def led_off(self, agt): # ação do ambiente: só executa o que o agente decidiu (agt: nome do agente, passado pelo MASPY)
        javino.sendMsg(self.ser, "ledOff")
        self.print("Sending a message to the serial port - Turn off")
        time.sleep(0.9)       
        self.perguntar(self.ser) # lê o novo estado na porta serial: o percept só muda se o Arduino confirmar
        time.sleep(0.9)       
    



class Basic_Agent(Agent):
    def __init__(self, agt_name=None):
        super().__init__(agt_name)
        self.add(Goal("analyze_environment"))

    # DELIBERAÇÃO: o agente escolhe o plano pelo contexto (a crença que ele tem sobre o LED)
    # equivale em AgentSpeak a:  +!analyze_environment : ledStatus(off) <- led_on.
    @pl(gain, Goal("analyze_environment"), Belief("ledStatus", "off", "Env"))
    def led_is_off(self, src): # *args: versões antigas do MASPY passam o valor do contexto ('off'/'on') como argumento extra
        self.print("Sucess reading the Environment")
        time.sleep(3)     
        self.print(f"Belief: {self.get(Belief('ledStatus', Any, 'Env'))}")
        time.sleep(0.2)      
        self.led_on()  # DECISÃO do agente: LED desligado -> ligar. A ao é executada pelo ambiente
        time.sleep(0.15)
        led = self.get(Belief("ledStatus", Any, "Env"))
        self.perceive("Env")
        print(led)
        self.add(Goal("analyze_environment"), instant=False) # recoloca o objetivo para o próximo ciclo (instant=False evita o plano rodar dentro dele mesmo)

    # equivale em AgentSpeak a:  +!analyze_environment : ledStatus(on) <- led_off.
    @pl(gain, Goal("analyze_environment"), Belief("ledStatus", "on", "Env"))
    def led_is_on(self, src): # *args: versões antigas do MASPY passam o valor do contexto ('off'/'on') como argumento extra
        self.print("Sucess reading the Environment")
        time.sleep(0.9)       
        self.print(f"Belief: {self.get(Belief('ledStatus', Any, 'Env'))}")
        time.sleep(0.9)       
        self.led_off()  # DECISÃO do agente: LED ligado -> desligar. A ação é executada pelo ambiente
        self.perceive("Env")  # percebe o ambiente agora: atualiza as crenças com o percept novo
        self.add(Goal("analyze_environment"), instant=False)

    # plano sem contexto: só é usado se nenhum dos dois acima se aplicar (precisa ficar por último)
    @pl(gain, Goal("analyze_environment"))
    def no_percept(self, src):
        self.print("No Percept on the Environment yet")
        self.chamar_perguntar()
        time.sleep(3)
        self.perceive("Env")
        led = self.get(Belief("ledStatus", Any, "Env"))
        self.perceive("Env") 
        if led:
            self.print("Sucess reading the initial percept")
            self.print(f"Belief: {self.get(Belief('ledStatus', Any, 'Env'))}")
        #self.perceive("Env")   # tenta de novo; se o ambiente não tiver o percept, ele ainda não existe
        self.add(Goal("analyze_environment"), instant=False)

        


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
    if ser: # javino.start devolve None se não conseguir abrir a porta (socat/SimulIDE fora do ar)
        env = Genneric_environment("Env", ser)
        time.sleep(2)
        agent = Basic_Agent("agent1")
        Admin().connect_to(agent, env)
        env._add_agent(agent)
        Admin().start_system() # bloqueia até o fim; Ctrl+C encerra o sistema
        time.sleep(4) # espera uma ação em andamento terminar antes de fechar a porta (senão dá erro depois do Ctrl+C)
        javino.disconnect(ser) # fecha a porta serial
    else:
        print("Não foi possível conectar à porta serial.")
    




    # no final de tudo colocar um time.sleep() para parar o loop de perceiving
