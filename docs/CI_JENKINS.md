# CI con Jenkins y Docker Compose

## Que incluye esta migracion

- Servicio `jenkins` en `docker-compose.yml` para arrancar junto a `db` y `web`.
- Imagen personalizada de Jenkins en `jenkins/Dockerfile` con Docker CLI.
- `Jenkinsfile` con etapas equivalentes a tu pipeline previo:
  - Lint (`ruff`)
  - Security (`bandit` y `pip-audit`)
  - Tests + coverage con PostgreSQL efimero
  - Docker build
  - Docker push en `main`

## Arranque de la plataforma

Desde la raiz del proyecto:

```bash
docker compose up -d --build
```

Servicios esperados:

- Django: `http://localhost:8000`
- Jenkins: `http://localhost:8080`

## Primer acceso a Jenkins

1. Obtener password inicial:

```bash
docker exec -it proyecto_jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

2. Abrir `http://localhost:8080` y completar setup.
3. Crear un Pipeline Job apuntando a este repo (`Jenkinsfile` en raiz).

## Credenciales requeridas

Para la etapa de push a Docker Hub, crear en Jenkins:

- Tipo: `Username with password`
- ID: `dockerhub-creds`
- Username: tu usuario Docker Hub
- Password: tu token Docker Hub

## Notas operativas

- El push solo corre en rama `main` y en builds que no son PR.
- Jenkins usa el socket Docker del host (`/var/run/docker.sock`) para ejecutar builds y contenedores efimeros de CI.
