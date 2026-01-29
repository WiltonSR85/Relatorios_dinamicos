from django.test import TestCase
from .construtores import ValidadorConsulta, ConstrutorConsulta
from setup.esquema import esquema_bd

consulta1 = {
    "fonte_principal": "Base",
    "colunas": [
        {
            "tabela_origem": "Base",
            "campo": "nome",
            "rotulo": "Nome da base",
            "agregacao": None
        },
        {
            "tabela_origem": "Base",
            "campo": "cidade",
            "rotulo": "Cidade",
            "agregacao": None
        },
        {
            "tabela_origem": "Unidade",
            "campo": "unidades_operacionais__id",
            "rotulo": "Número de unidades",
            "agregacao": "count"
        }
    ],
    "filtros": [],
    "ordenacoes": [
        {
            "campo": "unidades_operacionais__id",
            "ordem": "ASC",
            "agregacao": None
        }
    ],
    "limite": 50
}


class ValidadorConsultaTestCase(TestCase):
    def setUp(self):
        self.consulta = consulta1

    def test_validar_consulta_valida(self):
        validador = ValidadorConsulta(esquema_bd, self.consulta)
        consulta_valida = validador.validar()
        self.assertIn('app_model', consulta_valida)
        self.assertEqual(consulta_valida['app_model'], 'base.Base')
        # veriicar se os tipos foram adicionados
        for coluna in consulta_valida['colunas']:
            self.assertIn('tipo', coluna)

        
    """ def test_validar_consulta_invalida(self):
        consulta_invalida = self.consulta.copy()
        consulta_invalida['fonte_principal'] = 'FonteInexistente'
        validador = ValidadorConsulta(esquema_bd, consulta_invalida)
        with self.assertRaises(Exception):
            validador.validar()
        
    def test_validar_coluna_invalida(self):
        consulta_invalida = self.consulta.copy()
        consulta_invalida['colunas'][0]['campo'] = 'campo_inexistente'
        validador = ValidadorConsulta(esquema_bd, consulta_invalida)
        with self.assertRaises(Exception):
            validador.validar()

    def test_validar_agregacao_invalida(self):
        consulta_invalida = self.consulta.copy()
        consulta_invalida['colunas'][2]['agregacao'] = 'soma_invalida'
        validador = ValidadorConsulta(esquema_bd, consulta_invalida)
        with self.assertRaises(Exception):
            validador.validar()

    def test_validar_ordenacao_invalida(self):
        consulta_invalida = self.consulta.copy()
        consulta_invalida['ordenacoes'][0]['campo'] = 'campo_inexistente'
        validador = ValidadorConsulta(esquema_bd, consulta_invalida)
        with self.assertRaises(Exception):
            validador.validar() """

class ConstrutorConsultaTestCase(TestCase):
    def setUp(self):
        self.consulta = consulta1
        validador = ValidadorConsulta(esquema_bd, self.consulta)
        self.consulta_valida = validador.validar()
        self.construtor = ConstrutorConsulta(self.consulta_valida)
    
    def test_construir_filtros(self):
        filtros = self.construtor._construir_filtros()
        self.assertEqual(filtros, [])
    
    def test_construir_ordenacao(self):
        ordenacoes = self.construtor._construir_ordenacao()
        self.assertEqual(ordenacoes, ['unidades_operacionais__id'])

    
    
    