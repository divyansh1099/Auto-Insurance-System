# Admin Panel Documentation

## Overview

The admin panel provides comprehensive CRUD (Create, Read, Update, Delete) operations for managing all entities in the Telematics Insurance System.

## Features

### Admin Dashboard

- System-wide statistics (drivers, users, vehicles, devices, trips, events)
- Recent activity overview
- Quick access to all management sections

### Driver Management

- List all drivers with pagination and search
- View driver details
- Create new drivers
- Update driver information
- Delete drivers

### User Management

- List all users with pagination and search
- View user details
- Create new users (with admin/user role assignment)
- Update user information (including password reset)
- Delete users
- Toggle user active/inactive status

### Vehicle Management

- List all vehicles
- Filter by driver
- View vehicle details
- Delete vehicles

### Device Management

- List all telematics devices
- Filter by driver
- View device details
- Delete devices

### Trip Management

- List all trips
- Filter by driver
- View trip details
- Delete trips

### Event Management

- List telematics events
- Filter by driver and event type
- View event statistics

## Access Control

- **Admin Only**: All admin endpoints require admin authentication
- **Admin User**: Login with `admin` / `admin123` (or create via script)
- **Permission Check**: Backend validates `is_admin` flag on every request

## API Endpoints

### Dashboard

- `GET /api/v1/admin/dashboard/stats` - Get dashboard statistics

### Drivers

- `GET /api/v1/admin/drivers` - List drivers (with pagination & search)
- `GET /api/v1/admin/drivers/{driver_id}` - Get driver details
- `POST /api/v1/admin/drivers` - Create driver
- `PATCH /api/v1/admin/drivers/{driver_id}` - Update driver
- `DELETE /api/v1/admin/drivers/{driver_id}` - Delete driver

### Users

- `GET /api/v1/admin/users` - List users (with pagination & search)
- `GET /api/v1/admin/users/{user_id}` - Get user details
- `POST /api/v1/admin/users` - Create user
- `PATCH /api/v1/admin/users/{user_id}` - Update user
- `DELETE /api/v1/admin/users/{user_id}` - Delete user

### Vehicles

- `GET /api/v1/admin/vehicles` - List vehicles
- `GET /api/v1/admin/vehicles/{vehicle_id}` - Get vehicle details
- `DELETE /api/v1/admin/vehicles/{vehicle_id}` - Delete vehicle

### Devices

- `GET /api/v1/admin/devices` - List devices
- `GET /api/v1/admin/devices/{device_id}` - Get device details
- `DELETE /api/v1/admin/devices/{device_id}` - Delete device

### Trips

- `GET /api/v1/admin/trips` - List trips
- `GET /api/v1/admin/trips/{trip_id}` - Get trip details
- `DELETE /api/v1/admin/trips/{trip_id}` - Delete trip

### Events

- `GET /api/v1/admin/events` - List events
- `GET /api/v1/admin/events/stats` - Get event statistics

## Frontend Routes

- `/admin` - Admin Dashboard
- `/admin/drivers` - Manage Drivers
- `/admin/users` - Manage Users

## Setup

### 1. Create Admin User

The admin user is created automatically by the demo user script:

```bash
docker compose exec backend python /app/scripts/create_demo_users.py
```

Or manually via API:

```bash
curl -X POST http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123",
    "is_admin": true
  }'
```

### 2. Login as Admin

1. Navigate to `/login`
2. Enter credentials: `admin` / `admin123`
3. Admin menu will appear in sidebar

### 3. Access Admin Panel

After login, admin users will see:

- "Admin" section in sidebar
- Admin Dashboard link
- Manage Drivers link
- Manage Users link

## Usage

### Viewing Statistics

1. Navigate to Admin Dashboard (`/admin`)
2. View system-wide statistics
3. Check recent activity

### Managing Drivers

1. Navigate to Manage Drivers (`/admin/drivers`)
2. Use search to find specific drivers
3. Click "Edit" to modify driver information
4. Click "Delete" to remove driver (cascades to related data)

### Managing Users

1. Navigate to Manage Users (`/admin/users`)
2. View all users with their roles and status
3. Create new users with admin/user roles
4. Toggle user active/inactive status
5. Reset user passwords

## Security Notes

- All admin endpoints require authentication
- Admin check is performed on every request
- Users cannot delete their own account
- Password updates are hashed before storage
- Foreign key constraints prevent orphaned records

## Future Enhancements

- [ ] Full CRUD forms for creating/editing entities
- [ ] Bulk operations (delete multiple, export)
- [ ] Advanced filtering and sorting
- [ ] Audit log for admin actions
- [ ] Role-based permissions (super admin, admin, moderator)
- [ ] Data export functionality
- [ ] System health monitoring
- [ ] User activity logs
