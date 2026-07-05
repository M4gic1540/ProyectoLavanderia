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
        DOCKER_IMAGE = 'm4gic/main'
        VENV_DIR = '.venv-ci'
        // Eliminamos HAS_DOCKER de aquí para evitar conflictos de sobreescritura estática
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Detect toolchain') {
            steps {
                script {
                    // Evaluamos dinámicamente y lo asignamos explícitamente al entorno global
                    def dockerCheck = sh(
                        script: 'command -v docker >/dev/null 2>&1 && echo true || echo false',
                        returnStdout: true
                    ).trim()
                    
                    env.HAS_DOCKER = dockerCheck
                }
                sh '''
                    command -v python3 >/dev/null 2>&1 || {
                        echo "ERROR: python3 no esta disponible en el agente Jenkins."
                        exit 1
                    }
                    command -v pip3 >/dev/null 2>&1 || {
                        echo "ERROR: pip3 no esta disponible en el agente Jenkins."
                        exit 1
                    }
                    echo "Herramientas detectadas -> HAS_DOCKER: $HAS_DOCKER"
                '''
            }
        }

        stage('Setup Python env') {
            steps {
                sh '''
                    set -e
                    python3 -m venv "$VENV_DIR"
                    . "$VENV_DIR/bin/activate"
                    pip install --upgrade pip
                    pip install --no-cache-dir -r requirements.txt \
                      ruff==0.8.4 \
                      bandit==1.8.0 \
                      pip-audit==2.7.3 \
                      coverage==7.6.9
                '''
            }
        }

        stage('Lint (ruff)') {
            steps {
                sh '''
                    set -e
                    . "$VENV_DIR/bin/activate"
                    ruff check .
                    ruff format --check .
                '''
            }
        }

        stage('Security scan') {
            steps {
                sh '''
                    set -e
                    . "$VENV_DIR/bin/activate"
                    bandit -r . -x './*/migrations,./*/__pycache__,.venv,.venv-ci' -ll
                    pip-audit -r requirements.txt
                '''
            }
        }

        stage('Tests + Coverage') {
            steps {
                sh '''
                    set -e
                    . "$VENV_DIR/bin/activate"
                    export SECRET_KEY='ci-test-secret-key-not-for-production'
                    export DEBUG=False
                    export ALLOWED_HOSTS='localhost,127.0.0.1'
                    python manage.py makemigrations --check --dry-run
                    python manage.py check --deploy --fail-level WARNING
                    coverage run --source='users,core' \
                        --omit='*/migrations/*,*/__pycache__/*,manage.py,core/asgi.py,core/wsgi.py' \
                        manage.py test
                    coverage report -m --fail-under=90
                    coverage report -m --include='users/*.py,core/urls.py' \
                      --omit='users/tests.py' --fail-under=95
                    coverage xml
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'coverage.xml', allowEmptyArchive: false
                }
            }
        }

        stage('Docker build (validacion)') {
            when {
                expression { return env.HAS_DOCKER == 'true' }
            }
            steps {
                sh 'docker build -t proyecto-django:ci-$BUILD_NUMBER .'
            }
        }

        stage('Docker push') {
            when {
                expression {
                    return env.HAS_DOCKER == 'true' && env.BRANCH_NAME == 'main'
                }
            }
            environment {
                DOCKERHUB_CREDS = credentials('dockerhub-creds')
            }
            steps {
                sh '''
                    SHORT_SHA=$(git rev-parse --short HEAD)

                    echo "$DOCKERHUB_CREDS_PSW" | docker login \
                      -u "$DOCKERHUB_CREDS_USR" --password-stdin

                    docker tag proyecto-django:ci-$BUILD_NUMBER $DOCKER_IMAGE:latest
                    docker tag proyecto-django:ci-$BUILD_NUMBER $DOCKER_IMAGE:$SHORT_SHA

                    docker push $DOCKER_IMAGE:latest
                    docker push $DOCKER_IMAGE:$SHORT_SHA
                '''
            }
        }

        stage('Docker unavailable notice') {
            when {
                expression { return env.HAS_DOCKER != 'true' }
            }
            steps {
                echo 'Docker no disponible en el agente: se omitieron Docker build/push.'
            }
        }
    }

    post {
        always {
            cleanWs(deleteDirs: true)
        }
    }
}