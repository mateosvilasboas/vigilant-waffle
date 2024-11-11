# Desafio LuizaLabs//Estante Virual
Desafio técnico para Estante Virtual//LuizaLabs. FastAPI, SQLAlchemy e Docker.

## Descrição da API
A API do repositório cadastra e gerencia resultados de competições. Cada competição possui uma lista de atletas com seus respectivos resultados. A competição pode ser finalizada e a API pode retornar o ranking parcial ou final da pontuação dos atletas por competição.

## Instalação
A API depende de `Docker versão 27.3.1` ou superior. Em um terminal:

1. `git clone https://github.com/mateosvilasboas/vigilant-waffle.git`
2. `cd vigilante-waffle/`
3. `docker compose build`

## Inicialização
Para iniciar a aplicação, basta inserir em um terminal `docker compose up` e acessar em um navegador `localhost:8000/docs` para usar os endpoints. O arquivo de banco de dados é gerado no uso dos endpoints.

## Endpoints:

`GET /api/get-competitions`: retorna um lista com todas as competições cadastradas.

#### Response:
```json
{
  "competitions": [
    {
      "id": 1,
      "name": "dardos 100m",
      "unit": "meters",
      "number_of_attempts": 3,
      "is_finished": false,
      "athletes": []
    }
  ]
}
```

`GET /api/get-ranking/{name}`: retorna o ranking da competição `{name}` (não é case-sensitive) com somente a melhor pontuação do atleta, ordenado pela melhor pontuação do atleta. 

#### Response:
```json
{
  "is_finished": false,
  "unit": "meters",
  "ranking": [
    {
      "id": 2,
      "athlete": "lucas",
      "best_score": 4
    },
    {
      "id": 1,
      "athlete": "mateus",
      "best_score": 3
    }
  ]
}
```

`PUT /api/change-competition-status`: troca o status atual da competição (a competição será fechada se estiver aberta e vice versa). `name` é o nome da competição.

#### Payload
```json
{
  "name": "string"
}
```

#### Response
```json
{
  "competition": "dardos 100m",
  "is_finished": true
}
```

`POST /api/create-competition`: cria uma competição. O nome da competição (`name`) deve ser único e não é case-sensitive. A unidade de medida (`unit`) deve ser apenas `meters` ou `seconds`. `number_of_attempts` é a quantidade de pontuações por atleta aceita pela competição.

#### Payload
```json
{
  "name": "string",
  "unit": "string",
  "number_of_attempts": 1
}
```

#### Response
```json
"competition": {
    "id": 1,
    "name": "dardos 100m",
    "unit": "meters",
    "number_of_attempts": 3,
    "is_finished": false,
    "athletes": []
  }
```

`POST /api/create-result`: cria um resultado de um atleta em uma competição. `competition` se refere ao nome da competição. `scores` é uma lista de valores `float` cujo tamanho deve ser igual ao `number_of_attempts` da competição. Não é possível adicionar novos valores se a competição estiver terminada (`is_finished = true`).

#### Payload

```json
{
  "competition": "string",
  "athlete": "string",
  "scores": [
    1.0, 1.0, 1.0
  ]
}
```

#### Response
```json
{
  "result": {
    "id": 1,
    "name": "lucas",
    "competition_id": 1,
    "scores": [
      {
        "id": 1,
        "value": 4,
        "athlete_id": 2
      },
      {
        "id": 2,
        "value": 2,
        "athlete_id": 2
      },
      {
        "id": 3,
        "value": 1,
        "athlete_id": 1
      }
    ]
  }
}
```

## Devlog
A API foi desenvolvida usando Python e fastAPI, SQLAlchemy e SQLite. A ideia inicial era usar PostgreSQL no lugar do SQLite, porém tive dificuldades para inicializar o ambiente de desenvolvimento nos primeiros dias usando o PostgreSQL. Acredito que estava me equivocando na integração do sistema com o banco de dados usando Docker. Mas, como percebi que boa parte da documentação, blogs e videos sobre a stack utilizavam SQLite, optei por essa ferramenta para poder iniciar o desenvolvimento de fato e otimizar o tempo. 

Após início da programação da API, a maior dificuldade foi lidar com o SQLAlchemy. Nunca tinha usado a ORM para administrar queries e a princípio foi um pouco difícil me orientar pela documentação para construir os primeiros endpoints, mas eventualmente com a ajuda de outros materiais consegui modelar os dados e me situar. A partir dai o desenvolvimento fluiu mais tranquilamente.

Escolhi programar cinco endpoints na API, conforme as regras passadas. Um deles, o `get-competitions`, não necessariamente estava nas regras mas me ajudava bastante a visualizar os dados e as decisões de design que eu precisava tomar. 

Para um desenvolvimento futuro seria interessante adicionar novos endpoints (como de update e deleção de competições e atletas), além de melhoramentos nos endpoints de criação atuais, como a adição de funcionalidades de bulk insert dos elementos. Vale também uma nova tentativa para integrar o PostgreSQL com a API assim como estudo e upgrade da configuração do ambiente de desenvolvimento. 

## Testes

Para rodar os testes unitários da API, utilize `pytest` e insira no terminal `pytest` (utilizei o gerenciador de pacote `poetry`, logo meu rodei meus testes unitários com `poetry run pytest`)