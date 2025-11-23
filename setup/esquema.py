esquema_bd = {
  "Chamado": { 
    "label_tabela": "Chamado",
    "app_model": "chamado.Chamado",
    "campos": [
      { "label": "Motivo", "val": "motivo", "tipo": "string" },
      { "label": "Data/Hora Abertura", "val": "dataHora", "tipo": "datetime" },
      { "label": "Status", "val": "status", "tipo": "string" },
      { "label": "Número de Vítimas", "val": "numeroVitimas", "tipo": "number" },
      { "label": "É incidente?", "val": "inicidente", "tipo": "boolean" },
      { "label": "Cidade (Ocorrência)", "val": "cidade", "tipo": "string" },
      { "label": "Bairro (Ocorrência)", "val": "bairro", "tipo": "string" }
    ],
    "conexoes": [
      {
        "nome_amigavel": "Solicitante (Pessoa)",
        "campo_relacao": "solicitante",
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
        "nome_amigavel": "Histórico de Trâmites",
        "campo_relacao": "tramitechamado_set",
        "model_destino": "TramiteChamado"
      },
      {
        "nome_amigavel": "Unidade",
        "campo_relacao": "unidadechamado_set",
        "model_destino": "UnidadeChamado"
      }
    ]
  },
  "Pessoa": {
    "label_tabela": "Pessoa",
    "app_model": "pessoa.Pessoa",
    "campos": [
      { "label": "Nome completo", "val": "nome", "tipo": "string" },
      { "label": "Data Nascimento", "val": "dataNascimentoReal", "tipo": "date" },
      { "label": "Sexo", "val": "sexo", "tipo": "string" },
      { "label": "Telefone celular", "val": "telefoneCelular", "tipo": "string" }
    ],
    "conexoes": [
      {
        "nome_amigavel": "Usuário",
        "campo_relacao": "usuario",
        "model_destino": "User"
      },
      {
        "nome_amigavel": "Base",
        "campo_relacao": "baseCadastro",
        "model_destino": "Base"
      }
    ]
  },
  "AtendimentoPessoa": {
    "label_tabela": "Atendimento",
    "app_model": "chamado.AtendimentoPessoa",
    "campos": [
      { "label": "Queixa principal", "val": "queixa", "tipo": "text" },
      { "label": "Risco classificado", "val": "risco", "tipo": "string" },
      { "label": "Pressão arterial (PA)", "val": "pa", "tipo": "string" },
      { "label": "Pulso", "val": "pulso", "tipo": "string" },
      { "label": "Saturação O2", "val": "so2", "tipo": "string" },
      { "label": "Glicemia", "val": "glicemia", "tipo": "string" },
      { "label": "Glasgow", "val": "glasgow", "tipo": "string" },
      { "label": "Destino do paciente", "val": "destinoPaciente", "tipo": "string" },
      { "label": "Diagnóstico médico", "val": "diagnosticoMedico", "tipo": "string" },
      { "label": "Houve lesão traumática?", "val": "lesaoTraumatica", "tipo": "boolean" }
    ],
    "conexoes": [
      {
        "nome_amigavel": "Paciente",
        "campo_relacao": "paciente",
        "model_destino": "Pessoa"
      },
      {
        "nome_amigavel": "Chamado",
        "campo_relacao": "chamado",
        "model_destino": "Chamado"
      }
    ]
  },
  "Base": {
    "label_tabela": "Base",
    "app_model": "base.Base",
    "campos": [
      { "label": "Nome da base", "val": "nome", "tipo": "string" },
      { "label": "Cidade", "val": "cidade", "tipo": "string" },
      { "label": "Estado (UF)", "val": "estado", "tipo": "string" },
      { "label": "Bairro", "val": "bairro", "tipo": "string" }
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
        "model_destino": "User"
      },
      {
        "nome_amigavel": "Setor",
        "campo_relacao": "base_setor",
        "model_destino": "Setor"
      }
    ]
  },
  "Setor": {
    "label_tabela": "Setor",
    "app_model": "setor.Setor",
    "campos": [
      { "label": "Nome do setor", "val": "nome", "tipo": "string" },
      { "label": "Descrição", "val": "descricao", "tipo": "text" }
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
        "model_destino": "User"
      }
    ]
  },
  "Unidade": {
    "label_tabela": "Unidade",
    "app_model": "unidade.Unidade",
    "campos": [
      { "label": "Nome", "val": "nome", "tipo": "string" },
      { "label": "Tipo", "val": "tipo", "tipo": "string" },
      { "label": "Placa", "val": "placa", "tipo": "string" },
      { "label": "Modelo", "val": "modelo", "tipo": "string" },
      { "label": "Status Atual", "val": "status", "tipo": "string" }
    ],
    "conexoes": [
      {
        "nome_amigavel": "Base",
        "campo_relacao": "central",
        "model_destino": "Base"
      },
      {
        "nome_amigavel": "Alocação de unidade",
        "campo_relacao": "chamado_unidade",
        "model_destino": "UnidadeChamado"
      }
    ]
  },
  "UnidadeChamado": {
    "label_tabela": "Alocação de unidade",
    "app_model": "chamado.UnidadeChamado",
    "campos": [
      { "label": "Status no chamado", "val": "status", "tipo": "string" },
      { "label": "Data Alocação", "val": "alocado_em", "tipo": "datetime" }
    ],
    "conexoes": [
      {
        "nome_amigavel": "Unidade",
        "campo_relacao": "unidade",
        "model_destino": "Unidade"
      }
    ]
  },
  "User": {
    "label_tabela": "Usuário",
    "app_model": "django.contrib.auth.models.User",
    "campos": [
      { "label": "Username", "val": "username", "tipo": "string" },
      { "label": "E-mail", "val": "email", "tipo": "string" },
      { "label": "Ativo?", "val": "is_active", "tipo": "boolean" },
      { "label": "Staff?", "val": "is_staff", "tipo": "boolean" }
    ],
    "conexoes": []
  }
}