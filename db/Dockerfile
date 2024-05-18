FROM postgres:13

RUN echo "ALTER USER postgres PASSWORD 'Qq12345';" > /docker-entrypoint-initdb.d/change_password.sql

COPY init.sql /docker-entrypoint-initdb.d/
