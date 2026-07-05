pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        POSTGRES_DB = 'appdb_test'
        POSTGRES_USER = 'appuser'
        POSTGRES_PASSWORD = 'apppassword_ci'
        PYTHON_IMAGE = 'python:3.12-slim'
        DOCKER_IMAGE = 'm4gic/main'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Lint (ruff)') {
            steps {
                sh '''
                    docker run --rm \
                      -v "$PWD":/app \
                      -w /app \
                      $PYTHON_IMAGE \
                      sh -c "
                        pip install --no-cache-dir ruff==0.8.4 &&
                        ruff check . &&
                        ruff format --check .
                      "
                '''
            }
        }

        stage('Security scan') {
            steps {
                sh '''
                    docker run --rm \
                      -v "$PWD":/app \
                      -w /app \
                      $PYTHON_IMAGE \
                      sh -c "
                        pip install --no-cache-dir bandit==1.8.0 pip-audit==2.7.3 &&
                        bandit -r . -x './*/migrations,./*/__pycache__,.venv' -ll &&
                        pip-audit -r requirements.txt
                      "
                '''
            }
        }

        stage('Tests + Coverage') {
            steps {
                sh '''
                    set -e

                    NETWORK_NAME="ci_net_$BUILD_NUMBER"
                    POSTGRES_CONTAINER="ci_pg_$BUILD_NUMBER"

                    cleanup() {
                      docker rm -f "$POSTGRES_CONTAINER" >/dev/null 2>&1 || true
                      docker network rm "$NETWORK_NAME" >/dev/null 2>&1 || true
                    }

                    trap cleanup EXIT

                    docker network create "$NETWORK_NAME"

                    docker run -d \
                      --name "$POSTGRES_CONTAINER" \
                      --network "$NETWORK_NAME" \
                      -e POSTGRES_DB="$POSTGRES_DB" \
                      -e POSTGRES_USER="$POSTGRES_USER" \
                      -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
                      postgres:16

                                        until docker exec "$POSTGRES_CONTAINER" pg_isready \
                                            -U "$POSTGRES_USER" \
                                            -d "$POSTGRES_DB"; do
                      sleep 2
                    done

                    docker run --rm \
                      --network "$NETWORK_NAME" \
                      -v "$PWD":/app \
                      -w /app \
                      -e DB_ENGINE=postgres \
                      -e POSTGRES_HOST="$POSTGRES_CONTAINER" \
                      -e POSTGRES_PORT=5432 \
                      -e POSTGRES_DB="$POSTGRES_DB" \
                      -e POSTGRES_USER="$POSTGRES_USER" \
                      -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
                      -e SECRET_KEY='ci-test-secret-key-not-for-production' \
                      -e DEBUG=False \
                      -e ALLOWED_HOSTS='localhost,127.0.0.1' \
                      $PYTHON_IMAGE \
                      sh -c "
                        pip install --no-cache-dir -r requirements.txt coverage==7.6.9 &&
                        python manage.py makemigrations --check --dry-run &&
                        python manage.py check --deploy --fail-level WARNING &&
                                                COVERAGE_OMIT='*/migrations/*,*/__pycache__/*,manage.py,core/asgi.py,core/wsgi.py' &&
                                                coverage run --source='users,core' --omit="$COVERAGE_OMIT" \
                          manage.py test &&
                        coverage report -m --fail-under=90 &&
                        coverage report -m --include='users/*.py,core/urls.py' \
                          --omit='users/tests.py' --fail-under=95 &&
                        coverage xml
                      "
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'coverage.xml', allowEmptyArchive: false
                }
            }
        }

        stage('Docker build (validacion)') {
            steps {
                sh 'docker build -t proyecto-django:ci-$BUILD_NUMBER .'
            }
        }

        stage('Docker push') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKERHUB_USERNAME',
                        passwordVariable: 'DOCKERHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        SHORT_SHA=$(git rev-parse --short HEAD)

                        echo "$DOCKERHUB_TOKEN" | docker login \
                          -u "$DOCKERHUB_USERNAME" --password-stdin

                        docker tag proyecto-django:ci-$BUILD_NUMBER $DOCKER_IMAGE:latest
                        docker tag proyecto-django:ci-$BUILD_NUMBER $DOCKER_IMAGE:$SHORT_SHA

                        docker push $DOCKER_IMAGE:latest
                        docker push $DOCKER_IMAGE:$SHORT_SHA
                    '''
                }
            }
        }
    }

    post {
        always {
            cleanWs(deleteDirs: true)
        }
    }
}
