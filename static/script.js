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

        // Proceed to send the request if validation passes
        $.ajax({
            url: "/predict",
            type: "POST",
            data: { symptoms: symptoms },
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
                        fetchDetails(disease, "precautions_df");
                    });
                    $("#diets-btn").click(function () {
                        fetchDetails(disease, "diets");
                    });
                    $("#workout-btn").click(function () {
                        fetchDetails(disease, "workout_df");
                    });
                }
            },
            error: function () {
                alert("An error occurred. Please try again.");
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
                        type === "precautions_df" ? "#precautionModal" :
                        type === "diets" ? "#dietsModal" :
                        "#workoutModal";

                    $(modalId).find(".modal-body p").text(info);
                    $(modalId).modal("show");
                }
            },
            error: function () {
                alert("Failed to fetch details. Please try again.");
            }
        });
    }
});
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
$("#sendResultsBtn").click(function() {
    const predictedDisease = $("#resultText").text().replace("Predicted Disease: ", "");
    
    // Hide the prediction modal
    $("#resultModal").modal("hide");
    
    // Set the disease name
    $("#disease-result").text(`Disease: ${predictedDisease}`);
    
    // Fetch all details at once
    $.ajax({
        url: `/details/${predictedDisease}`,
        type: "GET",
        success: function(response) {
            if (response.error) {
                alert(response.error);
            } else {
                // Populate the results in the accordion
                $("#description-result").text(response.description);
                $("#medication-result").text(response.medication);
                $("#precaution-result").text(response.precautions_df);
                $("#diet-result").text(response.diets);
                $("#workout-result").text(response.workout_df);
                
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
            alert("Failed to fetch details. Please try again.");
        }
    });
});
// Handle email form submission
$("#emailResultsForm").on("submit", function(e) {
    e.preventDefault();
    
    const emailAddress = $("#emailAddress").val();
    const disease = $("#disease-result").text().replace("Disease: ", "");
    const description = $("#description-result").text();
    const medication = $("#medication-result").text();
    const precaution = $("#precaution-result").text();
    const diet = $("#diet-result").text();
    const workout = $("#workout-result").text();


    $("#spinner-overlay").removeClass("d-none");
    
    // Send the data to the server
$.ajax({
    url: "/send-results",
    type: "POST",
    data: {
        email: emailAddress,
        disease: disease,
        description: description,
        medication: medication,
        precaution: precaution,
        diet: diet,
        workout: workout
    },
    success: function(response) {
        if (response.success) {
            // Hide the modal first
            $("#resultsFormModal").modal("hide");
            
            // Add the flash message by making a server request to set it
            $.get("/set-flash-message", { type: "success", message: "Results have been sent to your email!" }, function() {
                // Reload the page to show the flash message
                window.location.reload();
            });
        } else {
            // Show error flash message
            $.get("/set-flash-message", 
                { type: "error", message: response.message || "Failed to send email. Please try again." }, 
                function() {
                    window.location.reload();
                }
            );
        }
    },
    error: function() {
        // Show error flash message for AJAX errors
        $.get("/set-flash-message", 
            { type: "error", message: "An error occurred while sending the email. Please try again." }, 
            function() {
                window.location.reload();
            }
        );
    }
});
});
//handle phone sms button
$("#usephonesendResultsBtn").click(function() {
    // Get the disease directly from the current modal
    const predictedDisease = $("#disease-result").text().replace("Disease: ", "");
    
    // Hide the current modal
    $("#resultsFormModal").modal("hide"); // Note: This should hide the results form modal
    
    // Copy all the data to the phone modal
    $("#usephoneresultsFormModal #disease-result").text(`Disease: ${predictedDisease}`);
    $("#usephoneresultsFormModal #description-result").html($("#description-result").html());
    $("#usephoneresultsFormModal #medication-result").html($("#medication-result").html());
    $("#usephoneresultsFormModal #precaution-result").html($("#precaution-result").html());
    $("#usephoneresultsFormModal #diet-result").html($("#diet-result").html());
    $("#usephoneresultsFormModal #workout-result").html($("#workout-result").html());
    
    // Get the user's phone from the server
    $.ajax({
        url: "/get-user-phone",
        type: "GET",
        success: function(phoneResponse) {
            if (phoneResponse.phone_number) {
                $("#phoneNumber").val(phoneResponse.phone_number);
            }
            
            // Show the phone results form modal
            $("#usephoneresultsFormModal").modal("show");
        },
        error: function() {
            // If we can't get the phone, still show the modal
            $("#usephoneresultsFormModal").modal("show");
        }
    });
});
// Hand send results on phone submission
// Handle phone form submission
$("#phoneResultsForm").on("submit", function(e) {
    e.preventDefault();
    
    const phoneNumber = $("#phoneNumber").val();
    const disease = $("#disease-result").text().replace("Disease: ", "");
    const description = $("#description-result").text();
    const medication = $("#medication-result").text();
    const precaution = $("#precaution-result").text();
    const diet = $("#diet-result").text();
    const workout = $("#workout-result").text();

    $("#spinner-overlay").removeClass("d-none");
    
    // Send the data to the server
    $.ajax({
        url: "/api/send-sms",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({
            phoneNumber: phoneNumber,
            data: {
                disease: disease,
                description: description,
                medication: medication,
                precaution: precaution,
                diet: diet,
                workout: workout
            }
        }),
        success: function(response) {
            if (response.success) {
                // Hide the modal first
                $("#usephoneresultsFormModal").modal("hide");
                
                // Add the flash message
                $.get("/set-flash-message", { 
                    type: "success", 
                    message: "Results have been sent to your phone!" 
                }, function() {
                    // Reload the page to show the flash message
                    window.location.reload();
                });
            } else {
                // Show error flash message
                $.get("/set-flash-message", { 
                    type: "error", 
                    message: response.message || "Failed to send SMS. Please try again." 
                }, function() {
                    window.location.reload();
                });
            }
        },
        error: function(xhr) {
            let errorMessage = "An error occurred while sending the SMS. Please try again.";
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMessage = xhr.responseJSON.message;
            }
            
            // Show error flash message for AJAX errors
            $.get("/set-flash-message", { 
                type: "error", 
                message: errorMessage 
            }, function() {
                window.location.reload();
            });
        },
        complete: function() {
            $("#spinner-overlay").addClass("d-none");
        }
    });
});
//populate user data from database
// Add this to your JavaScript to load user data when modal opens
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