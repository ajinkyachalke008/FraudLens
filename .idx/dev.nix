{ pkgs, ... }: {
  channel = "stable-24.05";

  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.nodejs_20
    pkgs.docker
    pkgs.docker-compose
    pkgs.postgresql_16
    pkgs.redis
    pkgs.git
    pkgs.curl
    pkgs.wget
    pkgs.jq
  ];

  env = {
    PYTHONPATH = "./backend";
  };

  idx = {
    extensions = [
      "ms-python.python"
      "ms-python.vscode-pylance"
      "bradlc.vscode-tailwindcss"
      "esbenp.prettier-vscode"
      "dbaeumer.vscode-eslint"
      "cweijan.vscode-postgresql-client2"
    ];

    workspace = {
      onCreate = {
        install-backend = "cd backend && pip install -r requirements.txt";
        install-frontend = "cd frontend && npm install";
        setup-db = "docker-compose up -d postgres neo4j redis kafka zookeeper";
      };

      onStart = {
        start-services = "docker-compose up -d";
        start-backend = "cd backend && uvicorn main:app --reload --port 8000";
        start-frontend = "cd frontend && npm run dev";
      };
    };

    previews = {
      enable = true;
      previews = {
        web = {
          command = ["npm" "run" "dev" "--prefix" "frontend"];
          manager = "web";
          env = { PORT = "$PORT"; };
        };
        api = {
          command = ["uvicorn" "main:app" "--reload" "--port" "8000" "--app-dir" "backend"];
          manager = "web";
          env = { PORT = "8000"; };
        };
      };
    };
  };
}
