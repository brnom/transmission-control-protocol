import asyncio
from tcputils import *
import os, sys

get_random_int = lambda: int.from_bytes(os.urandom(2), sys.byteorder)

class Servidor:
    expected_seq_no: int

    def __init__(self, rede, porta):
        self.rede = rede
        self.porta = porta
        self.conexoes = {}
        self.callback = None
        self.rede.registrar_recebedor(self._rdt_rcv)

    def registrar_monitor_de_conexoes_aceitas(self, callback):
        """
        Usado pela camada de aplicação para registrar uma função para ser chamada
        sempre que uma nova conexão for aceita
        """
        self.callback = callback

    # saida do ip e entrada do tcp
    def _rdt_rcv(self, src_addr, dst_addr, segment):
        src_port, dst_port, seq_no, ack_no, \
            flags, window_size, checksum, urg_ptr = read_header(segment)

        if dst_port != self.porta:
            # Ignora segmentos que não são destinados à porta do nosso servidor
            return
        if not self.rede.ignore_checksum and calc_checksum(segment, src_addr, dst_addr) != 0:
            print('descartando segmento com checksum incorreto')
            return

        payload = segment[4*(flags>>12):]
        id_conexao = (src_addr, src_port, dst_addr, dst_port)

        if (flags & FLAGS_SYN) == FLAGS_SYN:
            print('on init connection')
            # A flag SYN estar setada significa que é um cliente tentando estabelecer uma conexão nova

            conexao = self.conexoes[id_conexao] = Conexao(self, id_conexao)

            resp_seq_no = get_random_int()
            resp_ack_no = seq_no + 1
            resp_segment = make_header(dst_port, src_port, resp_seq_no, resp_ack_no, FLAGS_SYN|FLAGS_ACK)
            resp_fixed_segment = fix_checksum(resp_segment, dst_addr, src_addr)

            # Handshake aceitando a conexão
            self.rede.enviar(resp_fixed_segment, src_addr)

            # Sets expected sequence number
            self.expected_seq_no = seq_no + 1

            if self.callback:
                self.callback(conexao)
        elif id_conexao in self.conexoes:
            print('connection exists', id_conexao)
            # Passa para a conexão adequada se ela já estiver estabelecida
            self.conexoes[id_conexao]._rdt_rcv(seq_no, ack_no, flags, payload)
        else:
            print('%s:%d -> %s:%d (pacote associado a conexão desconhecida)' %
                  (src_addr, src_port, dst_addr, dst_port))


class Conexao:
    def __init__(self, servidor: Servidor, id_conexao):
        self.servidor = servidor
        self.id_conexao = id_conexao
        self.callback = None
        self.timer = asyncio.get_event_loop().call_later(1, self._exemplo_timer)  # um timer pode ser criado assim; esta linha é só um exemplo e pode ser removida
        #self.timer.cancel()   # é possível cancelar o timer chamando esse método; esta linha é só um exemplo e pode ser removida

    def _exemplo_timer(self):
        # Esta função é só um exemplo e pode ser removida
        print('Este é um exemplo de como fazer um timer')

    def _rdt_rcv(self, seq_no, ack_no, flags, payload):
        # check if seq_no is expected
        if seq_no != self.servidor.expected_seq_no:
            print('seq_no is not expected')
            return

        self.callback(self, payload)

        src_addr, src_port, dst_addr, dst_port = self.id_conexao
        resp_ack_no = seq_no + len(payload)
        segment = fix_checksum(make_header(src_port, dst_port, seq_no, resp_ack_no, flags), src_addr, dst_addr)

        self.servidor.rede.enviar(segment, dst_addr)
        self.servidor.expected_seq_no += len(payload)

    # Os métodos abaixo fazem parte da API

    def registrar_recebedor(self, callback):
        """
        Usado pela camada de aplicação para registrar uma função para ser chamada
        sempre que dados forem corretamente recebidos
        """
        self.callback = callback

    def enviar(self, dados):
        """
        Usado pela camada de aplicação para enviar dados
        """
        # TODO: implemente aqui o envio de dados.
        # Chame self.servidor.rede.enviar(segmento, dest_addr) para enviar o segmento
        # que você construir para a camada de rede.
        pass

    def fechar(self):
        """
        Usado pela camada de aplicação para fechar a conexão
        """
        # TODO: implemente aqui o fechamento de conexão
        pass
