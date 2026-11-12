from typing import Iterable

from maspy import *
from maspy.agent import Belief, Goal

class Real_World(Environment):
    def __init__(self, env_name):
        super().__init__(env_name)


class Basic_Agent(Agent):
    def __init__(self, agt_name=None):
        super().__init__(agt_name)
        self.add(Goal("say_hi"))

    @pl(gain, Goal("say_hi"))
    def analyzing(self, src):   
        self.print("hi") 
         
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
    env = Environment("Hardware")
    agent = Basic_Agent("agent1")
    Admin().start_system()
    