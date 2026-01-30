from django.test import TestCase
from django.core.exceptions import ValidationError
from .construtores import ValidadorConsulta, ConstrutorConsulta
from setup.esquema import esquema_bd
from copy import deepcopy

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
        
        for coluna in consulta_valida['colunas']:
            self.assertIn('tipo', coluna)
            self.assertIn('apelido', coluna)

    def test_validar_coluna_invalida(self):
        consulta_invalida = deepcopy(self.consulta)
        consulta_invalida['colunas'][0]['campo'] = 'responsavel__pessoa__usuario__password'
        validador = ValidadorConsulta(esquema_bd, consulta_invalida)
        with self.assertRaises(ValidationError):
            validador._resolver_caminho('responsavel__pessoa__usuario__password')

    def test_validar_limite_invalido(self):
        consulta_invalida = deepcopy(self.consulta)
        consulta_invalida['limite'] = 2000
        validador = ValidadorConsulta(esquema_bd, consulta_invalida)
        consulta_valida = validador.validar()
        self.assertEqual(consulta_valida['limite'], 1000)
    
    def test_validar_agregacao_invalida(self):
        consulta_invalida = deepcopy(self.consulta)
        consulta_invalida['colunas'][2]['agregacao'] = 'multiply'
        validador = ValidadorConsulta(esquema_bd, consulta_invalida)
        with self.assertRaises(ValidationError):
            validador.validar()

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

    
    
    