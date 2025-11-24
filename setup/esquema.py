esquema_bd = {
  "Chamado": { 
    "label_tabela": "Chamado",
    "app_model": "chamado.Chamado",
    "campos": [
      { "label": "Motivo", "valor": "motivo", "tipo": "string" },
      { "label": "Data/Hora Abertura", "valor": "dataHora", "tipo": "datetime" },
      { "label": "Status", "valor": "status", "tipo": "string" },
      { "label": "Número de Vítimas", "valor": "numeroVitimas", "tipo": "number" },
      { "label": "É incidente?", "valor": "inicidente", "tipo": "boolean" },
      { "label": "Cidade (Ocorrência)", "valor": "cidade", "tipo": "string" },
      { "label": "Bairro (Ocorrência)", "valor": "bairro", "tipo": "string" }
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
        "nome_amigavel": "Histórico de Trâmites",
        "campo_relacao": "tramitechamado_set",
        "model_destino": "TramiteChamado"
      },
      {
        "nome_amigavel": "UnidadeChamado",
        "campo_relacao": "unidade_chamado",
        "model_destino": "UnidadeChamado"
      }
    ]
  },
  "Pessoa": {
    "label_tabela": "Pessoa",
    "app_model": "pessoa.Pessoa",
    "campos": [
      { "label": "Nome completo", "valor": "nome", "tipo": "string" },
      { "label": "Data Nascimento", "valor": "dataNascimentoReal", "tipo": "date" },
      { "label": "Sexo", "valor": "sexo", "tipo": "string" },
      { "label": "Telefone celular", "valor": "telefoneCelular", "tipo": "string" }
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
      { "label": "Queixa principal", "valor": "queixa", "tipo": "text" },
      { "label": "Risco classificado", "valor": "risco", "tipo": "string" },
      { "label": "Pressão arterial (PA)", "valor": "pa", "tipo": "string" },
      { "label": "Pulso", "valor": "pulso", "tipo": "string" },
      { "label": "Saturação O2", "valor": "so2", "tipo": "string" },
      { "label": "Glicemia", "valor": "glicemia", "tipo": "string" },
      { "label": "Glasgow", "valor": "glasgow", "tipo": "string" },
      { "label": "Destino do paciente", "valor": "destinoPaciente", "tipo": "string" },
      { "label": "Diagnóstico médico", "valor": "diagnosticoMedico", "tipo": "string" },
      { "label": "Houve lesão traumática?", "valor": "lesaoTraumatica", "tipo": "boolean" }
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
      { "label": "Nome da base", "valor": "nome", "tipo": "string" },
      { "label": "Cidade", "valor": "cidade", "tipo": "string" },
      { "label": "Estado (UF)", "valor": "estado", "tipo": "string" },
      { "label": "Bairro", "valor": "bairro", "tipo": "string" }
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
      { "label": "Nome do setor", "valor": "nome", "tipo": "string" },
      { "label": "Descrição", "valor": "descricao", "tipo": "text" }
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
      { "label": "Nome", "valor": "nome", "tipo": "string" },
      { "label": "Tipo", "valor": "tipo", "tipo": "string" },
      { "label": "Placa", "valor": "placa", "tipo": "string" },
      { "label": "Modelo", "valor": "modelo", "tipo": "string" },
      { "label": "Status Atual", "valor": "status", "tipo": "string" }
    ],
    "conexoes": [
      {
        "nome_amigavel": "Base",
        "campo_relacao": "central",
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
    "label_tabela": "Alocação de unidade",
    "app_model": "chamado.UnidadeChamado",
    "campos": [
      { "label": "Status no chamado", "valor": "status", "tipo": "string" },
      { "label": "Data Alocação", "valor": "alocado_em", "tipo": "datetime" }
    ],
    "conexoes": [
      {
        "nome_amigavel": "Unidade",
        "campo_relacao": "unidade",
        "model_destino": "Unidade"
      },
      {
        "nome_amigavel": "Chamado",
        "campo_relacao": "chamado",
        "model_destino": "Chamado"
      }
    ]
  },
  "User": {
    "label_tabela": "Usuário",
    "app_model": "django.contrib.auth.models.User",
    "campos": [
      { "label": "Username", "valor": "username", "tipo": "string" },
      { "label": "E-mail", "valor": "email", "tipo": "string" },
      { "label": "Ativo?", "valor": "is_active", "tipo": "boolean" },
      { "label": "Staff?", "valor": "is_staff", "tipo": "boolean" }
    ],
    "conexoes": []
  }
}