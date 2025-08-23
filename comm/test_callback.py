# Define callback functions
def success_callback(result):
    print(f"Success: {result}")

def error_callback(error):
    print(f"Error: {error}")

# Main function that accepts callbacks
def process_data(data, on_success, on_error):
    try:
        # Simulate some processing
        if data > 0:
            result = data * 2
            # Call the success callback
            on_success(result)
        else:
            # Call the error callback
            on_error("Data must be positive")
    except Exception as e:
        on_error(str(e))

# Using the callbacks
print("Example 1: Success case")
process_data(5, success_callback, error_callback)

print("\nExample 2: Error case")
process_data(-1, success_callback, error_callback)

# You can also use lambda functions as callbacks
print("\nExample 3: Using lambda")
process_data(3, 
            lambda x: print(f"Lambda success: {x}"), 
            lambda e: print(f"Lambda error: {e}"))

# Or define callbacks inline
def custom_success(result):
    print(f"Custom processing: {result} squared = {result**2}")

print("\nExample 4: Custom callback")
process_data(4, custom_success, error_callback)


if __name__ == "__main__":
    # Example usage
    process_data(10, success_callback, error_callback)
    process_data(-5, success_callback, error_callback)