from flask import Flask, request, jsonify
from http import HTTPStatus
import sqlalchemy.exc

from data_model import Package
from connect_connector import SessionMaker

app = Flask(__name__)

def create_error_response(message, http_status_code):
    """Helper function to create a JSON error response consistent with the OpenAPI spec."""
    return jsonify({"code": http_status_code.value, "message": message}), http_status_code

@app.route('/', methods=['GET'])
def get_all_packages():
    """
    Retrieves all packages from the database.
    """
    try:
        with SessionMaker() as session:
            packages = session.query(Package).all()
            if not packages:
                return jsonify([]), HTTPStatus.OK  # Return empty list if no packages found
            # Convert Package objects to dictionaries
            package_list = [package.to_dict() for package in packages]
            return jsonify(package_list), HTTPStatus.OK
    except sqlalchemy.exc.SQLAlchemyError as e:
        # Log the database-specific error for internal review
        app.logger.error(f"Database error occurred: {e}")
        # Return a generic 500 error to the client
        return create_error_response("An error occurred while accessing the database.", HTTPStatus.INTERNAL_SERVER_ERROR)
    except Exception as e:
        # Log the unexpected error for internal review
        app.logger.error(f"An unexpected error occurred: {e}")
        # Return a generic 500 error to the client
        return create_error_response("An unexpected error occurred.", HTTPStatus.INTERNAL_SERVER_ERROR)
        

@app.route('/packages', methods=['GET'])
def get_package_info():
    """
    Retrieves package dimensions, weight, and special handling instructions
    for a given product ID.
    """
    product_id_str = request.args.get('product_id')

    # Validate product_id presence
    if not product_id_str:
        return create_error_response("product_id parameter is required.", HTTPStatus.BAD_REQUEST)

    # Validate product_id type
    try:
        product_id = int(product_id_str)
    except ValueError:
        return create_error_response("product_id must be an integer.", HTTPStatus.BAD_REQUEST)

    try:
        with SessionMaker() as session:
            # Query the database for the package
            package = session.query(Package).filter_by(product_id=product_id).first()

            if not package:
                return create_error_response(f"Package with product_id {product_id} not found.", HTTPStatus.NOT_FOUND)

            # Construct the response according to the OpenAPI spec
            # The spec requires integer types for dimensions and weight,
            # while the data_model.py uses Float. We cast to int here.
            # The spec uses camelCase for 'specialHandlingInstructions'.
            response_data = {
                "height": int(package.height),
                "width": int(package.width),
                "depth": int(package.depth),
                "weight": int(package.weight),
                "specialHandlingInstructions": package.special_handling_instructions
            }

            return jsonify(response_data), HTTPStatus.OK

    except sqlalchemy.exc.SQLAlchemyError as e:
        # Log the database-specific error for internal review
        app.logger.error(f"Database error occurred: {e}")
        # Return a generic 500 error to the client
        return create_error_response("An error occurred while accessing the database.", HTTPStatus.INTERNAL_SERVER_ERROR)
    except Exception as e:
        # Log the unexpected error for internal review
        app.logger.error(f"An unexpected error occurred: {e}")
        # Return a generic 500 error to the client
        return create_error_response("An unexpected error occurred.", HTTPStatus.INTERNAL_SERVER_ERROR)

if __name__ == '__main__':
    # For production environments, it's recommended to use a robust WSGI server
    # like Gunicorn or uWSGI instead of Flask's built-in development server.

    # The `create_tables()` function from `data_model.py` is responsible for
    # setting up the necessary database tables. This should typically be handled
    # as a separate setup step or by a migration tool before the application starts.
    # For example, you might run it once:
    #
    # from data_model import create_tables
    # from connect_connector import engine # engine is needed by create_tables
    # print("Attempting to create database tables if they don't exist...")
    # create_tables()
    # print("Table creation process finished.")

    app.run(host='0.0.0.0', port=8080, debug=False)  # Set debug=False for production or make it configurable