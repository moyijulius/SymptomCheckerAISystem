// Wait for the DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize DataTable with advanced features
           // Check if DataTable is already initialized
    if ($.fn.DataTable.isDataTable('#dataTable')) {
        dataTable = $('#dataTable').DataTable();
        dataTable.destroy(); // Destroy existing instance
    }
        const dataTable = $('#dataTable').DataTable({
            ordering: true,
            searching: true,
            paging: true,
            lengthChange: true,
            info: true,
            pageLength: 10,
            columnDefs: [
                { orderable: false, targets: [0, 5] }, // Disable sorting on checkbox and actions columns
                { searchable: false, targets: [0, 5] } // Disable searching on checkbox and actions columns
            ],
            dom: '<"d-flex justify-content-between align-items-center mb-3"f<"d-flex align-items-center"l<"ml-2"i>>>tp',
            language: {
                search: "_INPUT_",
                searchPlaceholder: "Search reports...",
                lengthMenu: "_MENU_ per page",
                info: "Showing _START_ to _END_ of _TOTAL_ reports",
                infoEmpty: "No reports available",
                emptyTable: "No reports available"
            }
        });

        // Select All checkbox functionality
    $('#selectAllReports').on('change', function() {
        $('.report-checkbox').prop('checked', $(this).prop('checked'));
        updateBulkDeleteButton();
    });

    // Individual checkboxes change event
    $(document).on('change', '.report-checkbox', function() {
        updateBulkDeleteButton();
        
        // Update "Select All" checkbox state
        const totalCheckboxes = $('.report-checkbox').length;
        const checkedCheckboxes = $('.report-checkbox:checked').length;
        $('#selectAllReports').prop('checked', totalCheckboxes === checkedCheckboxes && totalCheckboxes > 0);
    });

    // Function to update bulk delete button state
    function updateBulkDeleteButton() {
        const checkedCount = $('.report-checkbox:checked').length;
        $('#bulkDeleteBtn').prop('disabled', checkedCount === 0);
        
        if (checkedCount > 0) {
            $('#bulkDeleteBtn').text(`Delete Selected (${checkedCount})`);
        } else {
            $('#bulkDeleteBtn').text('Delete Selected');
        }
    }

    // View report button click handler
    $(document).on('click', '.view-report', function() {
        const reportId = $(this).data('report-id');
        loadReportDetails(reportId);
    });

    // Delete report button click handler
    $(document).on('click', '.delete-report', function() {
        const reportId = $(this).data('report-id');
        $('#deleteReportId').val(reportId);
    });

    // Confirm delete button click handler
    $('#confirmDeleteBtn').on('click', function() {
        const reportId = $('#deleteReportId').val();
        deleteReport(reportId);
    });

    // Bulk delete button click handler
    $('#bulkDeleteBtn').on('click', function() {
        const selectedIds = [];
        $('.report-checkbox:checked').each(function() {
            selectedIds.push($(this).val());
        });
        
        if (selectedIds.length > 0) {
            if (confirm(`Are you sure you want to delete ${selectedIds.length} selected reports? This action cannot be undone.`)) {
                bulkDeleteReports(selectedIds);
            }
        }
    });

    // Export report button click handler
    $(document).on('click', '.export-report', function() {
        const reportId = $(this).data('report-id');
        exportReport(reportId);
    });

    // Modal export button click handler
    $('#exportModalBtn').on('click', function() {
        const reportId = $('#deleteReportId').val();
        exportReport(reportId);
    });

    // Refresh table button click handler
    $('#refreshTableBtn').on('click', function() {
        // Show spinner in button
        const originalContent = $(this).html();
        $(this).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...');
        $(this).prop('disabled', true);
        
        // Fetch fresh data from server
        fetchReportData().then(function() {
            // Restore button state
            $('#refreshTableBtn').html(originalContent);
            $('#refreshTableBtn').prop('disabled', false);
        });
    });

    // Function to load report details into modal
    function loadReportDetails(reportId) {
        // Show spinner, hide details
        $('#reportModalSpinner').removeClass('d-none');
        $('#reportDetails').addClass('d-none');
        
        // Update delete button in modal with the correct report ID
        $('#deleteModalBtn').data('report-id', reportId);
        $('#deleteReportId').val(reportId);
        
        // Fetch report details from server
        fetch(`/admin/reports/${reportId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Populate modal with report data
            $('#modalUserId').text(data.user_id);
            $('#modalUserName').text(data.username || 'Not available');
            $('#modalUserEmail').text(data.email || 'Not available');
            $('#modalCreatedAt').text(data.created_at);
            $('#modalDisease').text(data.disease);
            $('#modalSymptoms').text(data.symptoms);
            $('#modalConfidence').html(`${data.confidence || 'N/A'} ${data.confidence ? `<div class="progress mt-1" style="height: 5px;"><div class="progress-bar" role="progressbar" style="width: ${data.confidence}%"></div></div>` : ''}`);
            
            // Populate tab content
            $('#description').html(data.description || '<p class="text-muted">No description available</p>');
            
            // Format precautions as a list if it contains bullet points
            if (data.precaution && data.precaution.includes('•')) {
                const precautionItems = data.precaution.split('•').filter(item => item.trim() !== '');
                let precautionHtml = '<ul class="mb-0">';
                precautionItems.forEach(item => {
                    precautionHtml += `<li>${item.trim()}</li>`;
                });
                precautionHtml += '</ul>';
                $('#precautions').html(precautionHtml);
            } else {
                $('#precautions').html(data.precaution || '<p class="text-muted">No precautions available</p>');
            }
            
            $('#medication').html(data.medication || '<p class="text-muted">No medication information available</p>');
            $('#diet').html(data.diet || '<p class="text-muted">No diet recommendations available</p>');
            $('#workout').html(data.workout || '<p class="text-muted">No workout recommendations available</p>');
            
            // Hide spinner, show details
            $('#reportModalSpinner').addClass('d-none');
            $('#reportDetails').removeClass('d-none');
        })
        .catch(error => {
            console.error('Error fetching report details:', error);
            $('#reportModalSpinner').addClass('d-none');
            $('#reportDetails').html(`<div class="alert alert-danger">Error loading report data: ${error.message}</div>`);
            $('#reportDetails').removeClass('d-none');
        });
    }

    // Function to delete a report
    function deleteReport(reportId) {
        // Show loading state
        $('#confirmDeleteBtn').prop('disabled', true);
        $('#confirmDeleteBtn').html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Deleting...');
        
        fetch(`/admin/reports/${reportId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Close the delete confirmation modal
            $('#deleteConfirmModal').modal('hide');
            
            // Close the view report modal if it's open
            $('#viewReportModal').modal('hide');
            
            // Remove the row from the table
            dataTable.row(`tr[data-report-id="${reportId}"]`).remove().draw();
            
            // Show success toast
            showToast('Report deleted successfully', 'success');
            
            // Reset button state
            $('#confirmDeleteBtn').prop('disabled', false);
            $('#confirmDeleteBtn').html('<i class="bi bi-trash"></i> Delete Permanently');
        })
        .catch(error => {
            console.error('Error deleting report:', error);
            showToast(`Error deleting report: ${error.message}`, 'error');
            
            // Reset button state
            $('#confirmDeleteBtn').prop('disabled', false);
            $('#confirmDeleteBtn').html('<i class="bi bi-trash"></i> Delete Permanently');
        });
    }

    // Function to bulk delete reports
    function bulkDeleteReports(reportIds) {
        // Show loading state
        $('#bulkDeleteBtn').prop('disabled', true);
        $('#bulkDeleteBtn').html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Deleting...');
        
        fetch('/admin/reports/bulk-delete', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ report_ids: reportIds })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Remove the rows from the table
            reportIds.forEach(id => {
                dataTable.row(`tr[data-report-id="${id}"]`).remove().draw(false);
            });
            
            // Show success toast
            showToast(`${reportIds.length} reports deleted successfully`, 'success');
            
            // Reset select all checkbox
            $('#selectAllReports').prop('checked', false);
            
            // Reset button state
            updateBulkDeleteButton();
        })
        .catch(error => {
            console.error('Error bulk deleting reports:', error);
            showToast(`Error deleting reports: ${error.message}`, 'error');
            
            // Reset button state
            updateBulkDeleteButton();
        });
    }

    // Function to export a report as PDF
    function exportReport(reportId) {
        window.open(`/admin/reports/${reportId}/export`, '_blank');
    }

    // Function to fetch fresh report data
    function fetchReportData() {
        return fetch('/admin/reports/data', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Clear existing data and add new data
            dataTable.clear();
            
            data.reports.forEach(report => {
                dataTable.row.add([
                    `<div class="form-check">
                        <input class="form-check-input report-checkbox" type="checkbox" value="${report.id}">
                    </div>`,
                    report.user_id,
                    report.disease,
                    report.symptoms.length > 50 ? report.symptoms.substring(0, 50) + '...' : report.symptoms,
                    report.created_at,
                    `<div class="btn-group btn-group-sm" role="group">
                        <button type="button" class="btn btn-info view-report" data-bs-toggle="modal" data-bs-target="#viewReportModal" data-report-id="${report.id}" title="View Report">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button type="button" class="btn btn-warning export-report" data-report-id="${report.id}" title="Export Report">
                            <i class="bi bi-download"></i>
                        </button>
                        <button type="button" class="btn btn-danger delete-report" data-bs-toggle="modal" data-bs-target="#deleteConfirmModal" data-report-id="${report.id}" title="Delete Report">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>`
                ]).node().dataset.reportId = report.id;
            });
            
            dataTable.draw();
            
            // Update statistics
            $('#total-users').text(data.stats.total_users);
            $('#active-users').text(data.stats.active_users);
            $('#total-reports').text(data.stats.total_reports);
            
            // Show success toast
            showToast('Report data refreshed successfully', 'success');
        })
        .catch(error => {
            console.error('Error fetching report data:', error);
            showToast(`Error refreshing data: ${error.message}`, 'error');
        });
    }

    // Toast notification function
    function showToast(message, type = 'success') {
        const background = type === 'success' ? '#4CAF50' : (type === 'info' ? '#3498db' : '#F44336');
        Toastify({
            text: message,
            duration: 3000,
            gravity: "top",
            position: "right",
            style: {
                background: background,
            },
            stopOnFocus: true,
            close: true,
            className: "toastify-custom",
        }).showToast();
    }

        
        // Helper function to get CSRF token
        function getCsrfToken() {
            return document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
        }
    });

    //export pdf
    function exportReport(reportId) {
        // Show loading state
        const exportBtn = $(`.export-report[data-report-id="${reportId}"]`);
        const originalContent = exportBtn.html();
        exportBtn.html('<span class="spinner-border spinner-border-sm" role="status"></span> Exporting...');
        exportBtn.prop('disabled', true);
        
        // Fetch PDF
        fetch(`/admin/reports/${reportId}/export`, {
            headers: {
                'Accept': 'application/pdf',
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => {
            if (!response.ok) throw new Error('Export failed');
            return response.blob();
        })
        .then(blob => {
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `medical_report_${reportId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
            
            // Show success toast
            showToast('Report exported successfully', 'success');
        })
        .catch(error => {
            console.error('Export error:', error);
            showToast('Error exporting report', 'error');
        })
        .finally(() => {
            // Restore button state
            exportBtn.html(originalContent);
            exportBtn.prop('disabled', false);
        });
    }