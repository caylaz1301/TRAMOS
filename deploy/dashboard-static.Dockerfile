FROM nginx:1.27-alpine

COPY deploy/nginx/dashboard-container.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
