"""
Esquema do banco de dados para construção dinâmica de consultas e relatórios.

Cada modelo possui campos e conexões com outros modelos.
Os campos incluem "rótulo" (nome que aparece para o usuário), "valor" (nome do campo no modelo) e "tipo" de dado (que não necessariamente é um tipo de dado do Python); o tipo de dado é utilizado para definir filtros e exibições apropriadas.
As conexões representam as associações entre modelos, permitindo navegação e junção de dados relacionados. O "nome_amigavel" é usado na interface para representar a conexão, "campo_relacao" é o campo no modelo atual que referencia o modelo de destino, e "model_destino" é o modelo relacionado. O nome do "model_destino" deve corresponder a uma chave neste dicionário.
"""

esquema_bd = {
  "Chamado": { 
    "app_model": "chamado.Chamado",
    "campos": [
      { "rotulo": "ID", "valor": "id", "tipo": "int"},
      { "rotulo": "Motivo", "valor": "motivo", "tipo": "string" },
      { "rotulo": "Status", "valor": "status", "tipo": "string" },
      { "rotulo": "Número de vítimas", "valor": "numero_vitimas", "tipo": "number" },
      { "rotulo": "É incidente?", "valor": "incidente", "tipo": "bool" },
      { "rotulo": "Cidade (Ocorrência)", "valor": "cidade", "tipo": "string" },
      { "rotulo": "Bairro (Ocorrência)", "valor": "bairro", "tipo": "string" }
    ],
    "conexoes": [
      {
        "nome_amigavel": "Pessoa",
        "campo_relacao": "pessoa",
        "model_destino": "Pessoa"
      },
      {
        "nome_amigavel": "Base",
        "campo_relacao": "base",
        "model_destino": "Base"
      },
      {
        "nome_amigavel": "Atendimentos",
        "campo_relacao": "atendimento_chamado",
        "model_destino": "AtendimentoPessoa"
      },
      {
        "nome_amigavel": "UnidadeChamado",
        "campo_relacao": "unidade_chamado",
        "model_destino": "UnidadeChamado"
      }
    ]
  },
  "Pessoa": {
    "app_model": "pessoa.Pessoa",
    "campos": [
      { "rotulo": "ID", "valor": "id", "tipo": "int"},
      { "rotulo": "Nome completo", "valor": "nome", "tipo": "string" },
      { "rotulo": "Data de nascimento", "valor": "dataNascimentoReal", "tipo": "date" },
      { "rotulo": "Sexo", "valor": "sexo", "tipo": "string" },
      { "rotulo": "Telefone celular", "valor": "telefoneCelular", "tipo": "string" }
    ],
    "conexoes": [
      {
        "nome_amigavel": "AtendimentoPessoa",
        "campo_relacao": "pessoa_atendimento",
        "model_destino": "AtendimentoPessoa"
      },
      {
        "nome_amigavel": "Base",
        "campo_relacao": "base_cadastro",
        "model_destino": "Base"
      },
      {
        "nome_amigavel": "Chamado",
        "campo_relacao": "chamado_set",
        "model_destino": "Chamado"
      },
      {
        "nome_amigavel": "Usuário",
        "campo_relacao": "usuario",
        "model_destino": "Usuário"
      }
    ]
  },
  "AtendimentoPessoa": {
    "app_model": "chamado.AtendimentoPessoa",
    "campos": [
      { "rotulo": "ID", "valor": "id", "tipo": "int"},
      { "rotulo": "Queixa principal", "valor": "queixa", "tipo": "string" },
      { "rotulo": "Risco classificado", "valor": "risco", "tipo": "string" },
      { "rotulo": "Pressão arterial (PA)", "valor": "pa", "tipo": "string" },
      { "rotulo": "Pulso", "valor": "pulso", "tipo": "string" },
      { "rotulo": "Saturação O2", "valor": "so2", "tipo": "string" },
      { "rotulo": "Glicemia", "valor": "glicemia", "tipo": "string" },
      { "rotulo": "Glasgow", "valor": "glasgow", "tipo": "string" },
      { "rotulo": "Destino do paciente", "valor": "destinoPaciente", "tipo": "string" },
      { "rotulo": "Diagnóstico médico", "valor": "diagnosticoMedico", "tipo": "string" },
      { "rotulo": "Houve lesão traumática?", "valor": "lesaoTraumatica", "tipo": "bool" }
    ],
    "conexoes": [
      {
        "nome_amigavel": "Chamado",
        "campo_relacao": "chamado",
        "model_destino": "Chamado"
      },
      {
        "nome_amigavel": "Pessoa",
        "campo_relacao": "pessoa",
        "model_destino": "Pessoa"
      }
    ]
  },
  "Base": {
    "app_model": "base.Base",
    "campos": [
      { "rotulo": "ID", "valor": "id", "tipo": "int"},
      { "rotulo": "Nome da base", "valor": "nome", "tipo": "string" },
      { "rotulo": "Cidade", "valor": "cidade", "tipo": "string" },
      { "rotulo": "Estado (UF)", "valor": "uf", "tipo": "string" },
      { "rotulo": "Bairro", "valor": "bairro", "tipo": "string" }
    ],
    "conexoes": [
      {
        "nome_amigavel": "Base central",
        "campo_relacao": "central",
        "model_destino": "Base"
      },
      {
        "nome_amigavel": "Responsável",
        "campo_relacao": "responsavel",
        "model_destino": "Usuário"
      },
      {
        "nome_amigavel": "Setor",
        "campo_relacao": "base_setor",
        "model_destino": "Setor"
      },
      {
        "nome_amigavel": "Unidade",
        "campo_relacao": "unidades_operacionais",
        "model_destino": "Unidade"
      }
    ]
  },
  "Setor": {
    "app_model": "setor.Setor",
    "campos": [
      { "rotulo": "ID", "valor": "id", "tipo": "int"},
      { "rotulo": "Nome do setor", "valor": "name", "tipo": "string" },
      { "rotulo": "Descrição", "valor": "descricao", "tipo": "string" }
    ],
    "conexoes": [
      {
        "nome_amigavel": "Base",
        "campo_relacao": "base",
        "model_destino": "Base"
      },
      {
        "nome_amigavel": "Membro",
        "campo_relacao": "membro",
        "model_destino": "Usuário"
      }
    ]
  },
  "Unidade": {
    "app_model": "unidade.Unidade",
    "campos": [
      { "rotulo": "ID", "valor": "id", "tipo": "int"},
      { "rotulo": "Nome da unidade", "valor": "nome", "tipo": "string" },
      { "rotulo": "Tipo", "valor": "tipo", "tipo": "string" },
      { "rotulo": "Placa", "valor": "placa", "tipo": "string" },
      { "rotulo": "Modelo", "valor": "modelo", "tipo": "string" },
      { "rotulo": "Status Atual", "valor": "status", "tipo": "string" }
    ],
    "conexoes": [
      {
        "nome_amigavel": "Base",
        "campo_relacao": "base",
        "model_destino": "Base"
      },
      {
        "nome_amigavel": "UnidadeChamado",
        "campo_relacao": "chamado_unidade",
        "model_destino": "UnidadeChamado"
      }
    ]
  },
  "UnidadeChamado": {
    "app_model": "chamado.UnidadeChamado",
    "campos": [
      { "rotulo": "ID", "valor": "id", "tipo": "int"},
      { "rotulo": "Status no chamado", "valor": "status", "tipo": "string" },
      { "rotulo": "Data de alocação", "valor": "alocado_em", "tipo": "datetime" }
    ],
    "conexoes": [
      {
        "nome_amigavel": "Chamado",
        "campo_relacao": "chamado",
        "model_destino": "Chamado"
      },
      {
        "nome_amigavel": "Unidade",
        "campo_relacao": "unidade",
        "model_destino": "Unidade"
      }
    ]
  },
  "Usuário": {
    "app_model": "django.contrib.auth.models.User",
    "campos": [
      { "rotulo": "Username", "valor": "username", "tipo": "string" },
      { "rotulo": "E-mail", "valor": "email", "tipo": "email" },
      { "rotulo": "Está ativo?", "valor": "is_active", "tipo": "bool" },
    ],
    "conexoes": [
        {
            "nome_amigavel": "Base",
            "campo_relacao": "resposavel_base",
            "model_destino": "Base"
        },
        {
            "nome_amigavel": "Pessoa",
            "campo_relacao": "pessoa",
            "model_destino": "Pessoa"
        }
    ]
  }
}