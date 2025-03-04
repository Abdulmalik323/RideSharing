from flask import Blueprint, request, jsonify
from db import get_db_connection

routes = Blueprint("routes", __name__)

#  Request a Ride
@routes.route("/request-ride", methods=["POST"])
def request_ride():
    data = request.json
    rider_id = data.get("rider_id")
    pickup_lat = data.get("pickup_lat")
    pickup_lng = data.get("pickup_lng")
    dropoff_lat = data.get("dropoff_lat")
    dropoff_lng = data.get("dropoff_lng")
    vehicle_type = data.get("vehicle_type")

    if not all([rider_id, pickup_lat, pickup_lng, dropoff_lat, dropoff_lng, vehicle_type]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Find an available vehicle of the requested type
        cursor.execute("""
            SELECT VehicleID FROM Vehicles WHERE VehicleType = %s LIMIT 1
        """, (vehicle_type,))
        vehicle = cursor.fetchone()

        if not vehicle:
            return jsonify({"error": "No vehicle available for type"}), 404

        vehicle_id = vehicle[0]

        # Insert new ride
        cursor.execute("""
            INSERT INTO Rides (RiderID, PickupLatitude, PickupLongitude, DropoffLatitude, DropoffLongitude, VehicleID, Status)
            VALUES (%s, %s, %s, %s, %s, %s, 'requested')
            RETURNING RideID
        """, (rider_id, pickup_lat, pickup_lng, dropoff_lat, dropoff_lng, vehicle_id))

        ride_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Ride requested", "ride_id": ride_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#  Accept a Ride
@routes.route("/accept-ride", methods=["POST"])
def accept_ride():
    data = request.json
    ride_id = data.get("ride_id")
    driver_id = data.get("driver_id")

    if not ride_id or not driver_id:
        return jsonify({"error": "Missing ride_id or driver_id"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("BEGIN")  # Start transaction

        # Lock ride row for update
        cursor.execute("""
            SELECT Status FROM Rides WHERE RideID = %s FOR UPDATE
        """, (ride_id,))
        ride = cursor.fetchone()

        if not ride or ride[0] != "requested":
            conn.rollback()
            return jsonify({"error": "Ride is no longer available"}), 400

        # Accept the ride
        cursor.execute("""
            UPDATE Rides SET Status = 'accepted', DriverID = %s WHERE RideID = %s
        """, (driver_id, ride_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Ride accepted"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
