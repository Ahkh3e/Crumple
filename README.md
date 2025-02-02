# Crumple

Crumple is a modern network topology designer and management tool that helps you visualize, plan, and manage your network infrastructure. With seamless NetBox integration and an intuitive interface, Crumple makes it easy to design and maintain complex network architectures.

![Crumple Dashboard](docs/images/dashboard.png)

## Features

- **Visual Network Design**: Drag-and-drop interface for creating network topologies
- **Device Management**: Track and manage network devices, servers, and their connections
- **NetBox Integration**: Seamlessly import and sync with your NetBox inventory
- **Cluster Management**: Organize devices into logical clusters
- **Real-time Updates**: Live status updates and monitoring
- **Interactive Visualization**: Dynamic network graphs using Cytoscape.js

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Node.js 16+ (for development)

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crumple.git
cd crumple
```

2. Start the application using Docker Compose:
```bash
docker-compose up -d
```

3. Access the application:
- Frontend: http://localhost:5000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Environment Configuration

1. Create environment files:
```bash
cp .env.example .env
```

2. Configure the following variables in `.env`:
```
BACKEND_URL=http://backend:8000
NETBOX_URL=your-netbox-url
NETBOX_TOKEN=your-netbox-token
```

## Usage

### Creating a Cluster

1. Click "New Cluster" in the sidebar
2. Enter cluster details and select devices
3. Arrange devices in the topology view
4. Save your cluster

### Managing Devices

1. Navigate to "Devices" in the sidebar
2. Add new devices or import from NetBox
3. Configure device specifications
4. Assign devices to clusters

### NetBox Integration

1. Go to "NetBox Integration" page
2. Configure your NetBox connection
3. Import device types and inventory
4. Keep your inventory in sync

## Development

For detailed development instructions, see [DEVELOPMENT.md](DEVELOPMENT.md).

### Local Development Setup

1. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements/dev.txt
```

2. Set up the frontend:
```bash
cd frontend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

3. Start the development servers:
```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
flask run --port 5000
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
python -m pytest
```

## Architecture

Crumple uses a modern, scalable architecture:

- **Frontend**: Flask + TailwindCSS
- **Backend**: FastAPI + SQLAlchemy
- **Database**: PostgreSQL
- **Visualization**: Cytoscape.js
- **Container**: Docker + Docker Compose

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Documentation: [docs/](docs/)
- Issue Tracker: [GitHub Issues](https://github.com/yourusername/crumple/issues)
- Discussion: [GitHub Discussions](https://github.com/yourusername/crumple/discussions)

## Acknowledgments

- [NetBox](https://github.com/netbox-community/netbox) for device inventory management
- [Cytoscape.js](https://js.cytoscape.org/) for network visualization
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Flask](https://flask.palletsprojects.com/) for the frontend framework
- [TailwindCSS](https://tailwindcss.com/) for styling
