#!/bin/bash
# =============================================================================
# AI Realtor - Enhanced Startup Script (SQLite Edition)
# =============================================================================
# This script handles:
# - Database initialization and migrations
# - Directory creation with proper permissions
# - Health checks before starting services
# - Automatic backup creation
# - Service monitoring
# =============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print banner
print_banner() {
    cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🏠 AI REALTOR PLATFORM                                  ║
║   SQLite Edition - Production Ready                       ║
║                                                           ║
║   FastAPI Backend  → http://localhost:8000                ║
║   API Documentation → http://localhost:8000/docs          ║
║   MCP Server       → http://localhost:8001                ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
}

# Create necessary directories
setup_directories() {
    log_info "Setting up directories..."

    mkdir -p /app/data
    mkdir -p /app/data/backups
    mkdir -p /app/logs

    log_success "Directories created"
}

# Backup existing database if it exists
backup_database() {
    local db_path="/app/data/ai_realtor.db"

    if [ -f "$db_path" ]; then
        local backup_path="/app/data/backups/ai_realtor_$(date +%Y%m%d_%H%M%S).db"
        log_info "Backing up existing database..."
        cp "$db_path" "$backup_path"
        log_success "Database backed up to: $backup_path"

        # Keep only last 5 backups
        ls -t /app/data/backups/*.db 2>/dev/null | tail -n +6 | xargs -r rm --
        log_info "Cleaned old backups (kept last 5)"
    fi
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."

    if alembic upgrade head; then
        log_success "Database migrations completed successfully"
    else
        log_warning "Migration failed - this might be normal on first run"
        log_info "Attempting to create database from scratch..."

        # Try to create the database
        alembic revision --autogenerate -m "Initial migration" || true
        alembic upgrade head || log_error "Failed to create database"
    fi
}

# Verify database
verify_database() {
    local db_path="/app/data/ai_realtor.db"

    if [ -f "$db_path" ]; then
        local size=$(du -h "$db_path" | cut -f1)
        log_success "Database verified: $db_path (Size: $size)"

        # Show table count
        local tables=$(sqlite3 "$db_path" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo "0")
        log_info "Database contains $tables tables"
    else
        log_warning "Database file not found at $db_path"
    fi
}

# Create initial data if needed
seed_database() {
    log_info "Checking if initial data seeding is needed..."

    # This could be used to create default admin user, etc.
    # For now, we'll skip this
    log_info "No seeding required"
}

# Start services
start_services() {
    log_info "Starting services via supervisor..."

    # Start supervisor in foreground
    exec supervisord -c /etc/supervisor/conf.d/supervisord.conf
}

# Main startup sequence
main() {
    print_banner

    log_info "Starting AI Realtor Platform..."
    log_info "Database: SQLite"
    log_info "Data directory: /app/data"

    echo ""

    # Run startup sequence
    setup_directories
    backup_database
    run_migrations
    verify_database
    seed_database

    echo ""
    log_success "Initialization complete!"
    echo ""

    # Start services (this will block)
    start_services
}

# Run main function
main "$@"
