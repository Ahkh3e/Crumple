# Crumple - Netbox Cluster Visualizer

Crumple is a web-based tool for visualizing and managing Netbox clusters. It provides an interactive interface to view, modify, and sync cluster configurations using Cytoscape.js for visualization.

## Features

- Interactive cluster visualization using Cytoscape.js
- Real-time synchronization with Netbox
- Multiple layout options for cluster visualization
- Device and interface information display
- Export cluster configurations to YAML
- Persistent layout saving
- Asynchronous task processing with RabbitMQ

## Architecture

- **Frontend**: Flask templates with Cytoscape.js for visualization (Port 3000)
- **Backend**: Python Flask application
- **Database**: PostgreSQL 14 for storing cluster data
- **Message Queue**: RabbitMQ for async task processing
- **Containerization**: Docker with isolated network architecture

## Network Architecture

The application uses a two-tier network architecture for security:

1. Frontend Network (`crumple_frontend`):
   - Only the web service is connected
   - Port 3000 exposed for web access
   - Allows external access to the web interface

2. Backend Network (`crumple_backend`):
   - Internal network for services
   - No external connectivity
   - Services: PostgreSQL, RabbitMQ, worker
   - Secure communication between components

Services communicate using internal Docker DNS names:
- PostgreSQL: `postgres:5432`
- RabbitMQ: `rabbitmq:5672`
- Netbox: Configurable via web interface

## Prerequisites

- Docker and Docker Compose
- Netbox instance (accessible from Docker network)
- Python 3.11+ (for development)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crumple.git
cd crumple
```

2. Create a `.env` file from the example:
```bash
cp .env.example .env
```

3. Configure your environment:
   - Set your secret key
   - Adjust any other settings as needed
   - Internal service URLs are pre-configured

4. Build and start the containers:
```bash
docker-compose up --build
```

The application will be available at `http://localhost:3000`

## Configuration

### Internal Services
- PostgreSQL runs on the internal network only
- RabbitMQ runs on the internal network only
- Worker service connects to internal network only

### Netbox Configuration
1. Access the settings page at `http://localhost:3000/settings`
2. Enter your Netbox URL and API token
3. Test the connection
4. Save settings to start using the application

## Development

For local development without Docker:

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up local services:
   - Install PostgreSQL 14
   - Install RabbitMQ
   - Configure .env with local service addresses

4. Run the development server:
```bash
flask run -p 3000
```

## Database Management

```bash
# Inside the web container
flask db init     # First time only
flask db migrate  # Create migration
flask db upgrade  # Apply migration
```

## Docker Commands

```bash
# Build and start services
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Reset data (use with caution)
docker-compose down -v
```

## Security Notes

- Only the web service port (3000) is exposed
- All sensitive services are isolated in the internal network
- Netbox credentials stored securely in database
- Use environment variables for all sensitive configuration
- Consider using Docker secrets for production deployments
- Set up proper authentication for production use

## Network Troubleshooting

1. Service Discovery:
   - All services use Docker DNS names
   - Services on backend network: postgres, rabbitmq
   - Web service has access to both networks

2. Connection Issues:
   - Check network isolation
   - Verify service health checks
   - Review container logs

3. External Services:
   - Configure Netbox connection through settings UI
   - Ensure network routing is correct
   - Check firewall rules if needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
