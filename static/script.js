$(document).ready(function () {
    // Real-time input validation
    document.getElementById('symptoms').addEventListener('input', function (e) {
        const input = e.target.value;
        const errorMessage = document.getElementById('errorMessage');
        if (/[^a-zA-Z,_\s]/.test(input)) {
            errorMessage.textContent = "Only letters, commas, spaces, and underscores are allowed.";
        } else {
            errorMessage.textContent = "";
        }
    });

    $("#symptom-form").on("submit", function (e) {
        e.preventDefault();

        const symptoms = $("#symptoms").val().trim();
        const errorMessage = $("#errorMessage");

        // Validate the input first
        if (symptoms === "") {
            errorMessage.text("Input symptoms first");
            return; // Stop further processing
        } else {
            errorMessage.text(""); // Clear the error message
        }

        // Get CSRF token from meta tag
        const csrfToken = $('meta[name="csrf-token"]').attr('content');

        // Proceed to send the request if validation passes
        $.ajax({
            url: "/predict",
            type: "POST",
            data: { 
                symptoms: symptoms,
                csrf_token: csrfToken  // Include CSRF token in data
            },
            headers: {
                'X-CSRFToken': csrfToken  // Also send as header
            },
            success: function (response) {
                if (response.error) {
                    alert(response.error); // Show error from server
                } else {
                    const disease = response.disease;
                    $("#resultText").text(`Predicted Disease: ${disease}`);
                    $("#resultModal").modal("show");

                    // Add buttons for additional details
                    $("#dynamic-buttons").html(`
                        <h1>Our AI Systems</h1>
                        <div class="floating-buttons-container">
                            <button class="btn btn-info bg-warning" id="medication-btn">Medication</button>
                            <button class="btn btn-info bg-success" id="description-btn">Description</button>
                            <button class="btn btn-info bg-danger" id="precaution-btn">Precaution</button>
                            <button class="btn btn-info bg-info" id="diets-btn">Diets</button>
                            <button class="btn btn-info bg-primary" id="workout-btn">Workout</button>
                        </div>
                    `);

                    // Fetch and display details when buttons are clicked
                    $("#medication-btn").click(function () {
                        fetchDetails(disease, "medication");
                    });
                    $("#description-btn").click(function () {
                        fetchDetails(disease, "description");
                    });
                    $("#precaution-btn").click(function () {
                        fetchDetails(disease, "precautions");
                    });
                    $("#diets-btn").click(function () {
                        fetchDetails(disease, "diets");
                    });
                    $("#workout-btn").click(function () {
                        fetchDetails(disease, "workout_df");
                    });
                }
            },
            error: function (xhr, status, error) {
                console.error("Error:", xhr.responseText);
                alert("An error occurred. Please try again. Error: " + xhr.responseText);
            }
        });
    });

    function fetchDetails(disease, type) {
        $.ajax({
            url: `/details/${disease}`,
            type: "GET",
            success: function (response) {
                if (response.error) {
                    alert(response.error);
                } else {
                    const info = response[type];
                    const modalId =
                        type === "medication" ? "#medicationModal" :
                        type === "description" ? "#descriptionModal" :
                        type === "precautions" ? "#precautionModal" :
                        type === "diets" ? "#dietsModal" :
                        "#workoutModal";
                    
                    // Special handling for precautions which is now an array
                    if (type === "precautions" && Array.isArray(info)) {
                        const modalBody = $(modalId).find(".modal-body");
                        modalBody.empty(); // Clear previous content
                        
                        // Create a list for precautions
                        const precautionsList = $('<ul class="list-group"></ul>');
                        
                        // Add each precaution as a list item
                        info.forEach(precaution => {
                            precautionsList.append(`<li class="list-group-item">${precaution}</li>`);
                        });
                        
                        modalBody.append(precautionsList);
                    } else {
                        // Handle other types as before
                        $(modalId).find(".modal-body").html(`<p>${info}</p>`);
                    }
                    
                    $(modalId).modal("show");
                }
            },
            error: function () {
                alert("Failed to fetch details. Please try again.");
            }
        });
    }
});
    function fetchDetails(disease, type) {
        $.ajax({
            url: `/details/${disease}`,
            type: "GET",
            success: function (response) {
                if (response.error) {
                    alert(response.error);
                } else {
                    const info = response[type];
                    const modalId =
                        type === "medication" ? "#medicationModal" :
                        type === "description" ? "#descriptionModal" :
                        type === "precautions" ? "#precautionModal" :
                        type === "diets" ? "#dietsModal" :
                        "#workoutModal";
                    
                    // Special handling for precautions which is now an array
                    if (type === "precautions" && Array.isArray(info)) {
                        const modalBody = $(modalId).find(".modal-body");
                        modalBody.empty(); // Clear previous content
                        
                        // Create a list for precautions
                        const precautionsList = $('<ul class="list-group"></ul>');
                        
                        // Add each precaution as a list item
                        info.forEach(precaution => {
                            precautionsList.append(`<li class="list-group-item">${precaution}</li>`);
                        });
                        
                        modalBody.append(precautionsList);
                    } else {
                        // Handle other types as before
                        $(modalId).find(".modal-body").html(`<p>${info}</p>`);
                    }
                    
                    $(modalId).modal("show");
                }
            },
            error: function () {
                alert("Failed to fetch details. Please try again.");
            }
        });
    }

// Wait for the page to fully load
document.addEventListener("DOMContentLoaded", function() {
    // Select all flash messages
    let flashMessages = document.querySelectorAll(".alert");

    flashMessages.forEach(function(message) {
        // Set a timeout to remove the message after 3 seconds (3000ms)
        setTimeout(function() {
            message.style.transition = "opacity 0.5s";
            message.style.opacity = "0"; // Fade out
            setTimeout(() => message.remove(), 500); // Remove from DOM
        }, 3000);
    });
});
// Handle "Take Action" button click
// Update this part in your $("#sendResultsBtn").click() function
$("#sendResultsBtn").click(function() {
    const predictedDisease = $("#resultText").text().replace("Predicted Disease: ", "");
    
    // Hide the prediction modal
    $("#resultModal").modal("hide");
    
    // Set the disease name
    $("#disease-result").text(`Disease: ${predictedDisease}`);
    
    // Show spinner while loading
    $("#spinner-overlay").removeClass("d-none");
    
    // Fetch all details at once
    $.ajax({
        url: `/details/${predictedDisease}`,
        type: "GET",
        success: function(response) {
            if (response.error) {
                alert(response.error);
                $("#spinner-overlay").addClass("d-none");
            } else {
                // Populate the results in the accordion
                $("#description-result").text(response.description);
                $("#medication-result").text(response.medication);
                
                // Special handling for precautions which is now an array
                if (Array.isArray(response.precautions)) {
                    const precautionsList = $('<ul class="list-group"></ul>');
                    response.precautions.forEach(precaution => {
                        precautionsList.append(`<li class="list-group-item">${precaution}</li>`);
                    });
                    $("#precaution-result").empty().append(precautionsList);
                } else {
                    $("#precaution-result").text(response.precautions || "No precautions available.");
                }
                
                $("#diet-result").text(response.diets);
                $("#workout-result").text(response.workout_df);
                
                // Hide spinner after loading
                $("#spinner-overlay").addClass("d-none");
                
                // Get the user's email from the server
                $.ajax({
                    url: "/get-user-email",
                    type: "GET",
                    success: function(emailResponse) {
                        if (emailResponse.email) {
                            $("#emailAddress").val(emailResponse.email);
                        }
                        
                        // Show the results form modal
                        $("#resultsFormModal").modal("show");
                    },
                    error: function() {
                        // If we can't get the email, still show the modal
                        $("#resultsFormModal").modal("show");
                    }
                });
            }
        },
        error: function() {
            $("#spinner-overlay").addClass("d-none");
            alert("Failed to fetch details. Please try again.");
        }
    });
});
//populate user data from database
//to get the profile data automatically
document.querySelector('[data-bs-target="#profileModal"]').addEventListener('click', function() {
    fetch('/get_profile_data')
        .then(response => response.json())
        .then(data => {
            document.getElementById('username').value = data.username;
            document.getElementById('email').value = data.email;
            document.getElementById('phone').value = data.phone_number;
            document.getElementById('age').value = data.age;
            document.getElementById('gender').value = data.gender;
        });
});

//Update 
// Update profile button event handler
document.getElementById('updateProfile').addEventListener('click', function() {
    const formData = new FormData(document.getElementById('profileForm'));
    
    // Log form data for debugging
    for (let [key, value] of formData.entries()) {
        console.log(key, value);
    }
    
    fetch('/update_profile', {
        method: 'POST',
        body: formData,
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Display success message inline
        const successMessage = document.getElementById('successMessage');
        if (successMessage) {
            successMessage.textContent = data.message; // Set the success message
            successMessage.classList.remove('d-none'); // Make the message visible
        }

        // Close the modal after successful update
        const modal = bootstrap.Modal.getInstance(document.getElementById('profileModal'));
        if (modal) {
            modal.hide();
        }
        
        // Create a global success message if needed
        createGlobalAlert('success', data.message);

        // Optionally, hide the success message after a few seconds
        if (successMessage) {
            setTimeout(() => {
                successMessage.classList.add('d-none');
            }, 5000); // Hide after 5 seconds
        }
    })
    .catch(error => {
        console.error('Error:', error);

        // Display error message inline
        const successMessage = document.getElementById('successMessage');
        if (successMessage) {
            successMessage.textContent = 'Failed to update profile. Please try again later.';
            successMessage.classList.remove('d-none');
            successMessage.classList.remove('alert-success'); // Remove success styling
            successMessage.classList.add('alert-danger'); // Add error styling

            // Optionally, hide the error message after a few seconds
            setTimeout(() => {
                successMessage.classList.add('d-none');
                successMessage.classList.remove('alert-danger'); // Reset styling
                successMessage.classList.add('alert-success'); // Reset styling
            }, 5000); // Hide after 5 seconds
        } else {
            // Create a global error alert
            createGlobalAlert('danger', 'Failed to update profile. Please try again later.');
        }
    });
});

// Helper function to create global alerts
function createGlobalAlert(type, message) {
    // Check if there's already a container for alerts
    let alertContainer = document.getElementById('global-alerts');
    
    // If not, create one
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'global-alerts';
        alertContainer.className = 'position-fixed top-0 start-50 translate-middle-x mt-3';
        alertContainer.style.zIndex = '9999';
        document.body.appendChild(alertContainer);
    }
    
    // Create the alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.role = 'alert';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add the alert to the container
    alertContainer.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => {
            alert.remove();
            
            // Remove the container if it's empty
            if (alertContainer.children.length === 0) {
                alertContainer.remove();
            }
        }, 150);
    }, 5000);
}