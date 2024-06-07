var fetchInterval;
var lastStepNo = 0;
$(document).ready(function() {
    Reset();
    $('#submitAlgorithm').click(function(e) {
        e.preventDefault();
        var selectedAlgorithm = $('input[name="algorithm"]:checked').val();
        $.ajax({
            url: '/set_algorithm',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({algorithm: selectedAlgorithm}),
            success: function(response) {
                console.log('Algorithm set successfully');
            },
            error: function(error) {
                console.log('Error setting algorithm');
            }
        });
    });

    $('#Start').click(function() {
        triggerAction();
    });

    $('#Clear').click(function() {
        Reset();
    });

    $('#Pause').click(function() {
        var $this = $(this);  
        if ($this.text() === '暂停') {
            $this.text('继续'); 
        } else {
            $this.text('暂停'); 
        }
        Pause();
    });

    $('#oneCmd').click(function() {
        change_single_command();
    });

    $('#conCmd').click(function() {
        change_process_method();
    });

    function fetchMemoryStatus() {
        $.ajax({
            url: '/get_memory_status',
            type: 'GET',
            success: function(data) {
                if (data.memory_blocks) {
                    updateMemoryTable(data.memory_blocks);
                }
                if (data.extra_stats) {
                    updateResults(data.extra_stats);  
                }
                if (data.swap_info) { 
                    updateSwapInfo(data.swap_info);
                }
            },
            error: function() {
                console.log('Error fetching memory status');
            }
        });
    }

    function updateMemoryTable(memoryBlocks) {
        for (var i = 0; i < memoryBlocks.length; i++) {
            var page = memoryBlocks[i];
            if (page !== null) {
                var tableHtml = '<table>';
                page.content.forEach(function(command) {
                    var color = command.handled === 0 ? 'white' : command.handled === 1?'skyblue':'lightgray';
                    tableHtml += `<tr class="command-row" style="background-color:${color}; height:50px; font-size:15px;"><td>${command.No}</td></tr>`;
                });
                tableHtml += '</table>';
            $(`.memory-block:eq(${i})`).html(tableHtml);
            } else {
            $(`.memory-block:eq(${i})`).html(''); 
            }
        }
    }

    function updateResults(stats) {
        $('#faultCount').text(stats.faultCount);
        $('#faultRate').text((stats.faultRate * 100).toFixed(2) + '%');
    }
    
    function updateSwapInfo(swapInfo) {
        if (swapInfo.StepNo !== lastStepNo) {
            lastStepNo = swapInfo.StepNo;
            if (swapInfo.Count > 0 && swapInfo.Count <= 320) {
                var newRow = `<tr>
                    <td>${swapInfo.Count}</td>
                    <td>${swapInfo.StepNo}</td>
                    <td>${swapInfo.status ? '是' : '否'}</td>
                    <td>${swapInfo.inpage === -1 ? '-' : swapInfo.inpage}</td>
                    <td>${swapInfo.outpage === -1 ? '-' : swapInfo.outpage}</td>
                </tr>`;
                $('.info_table tbody').append(newRow);
                var $tableContainer = $('.table-container');
                $tableContainer.scrollTop($tableContainer.prop("scrollHeight"));
            }
        }
    }
    
    function triggerAction() {
        $('#Start').prop('disabled', true);
        fetchInterval = setInterval(fetchMemoryStatus, 100);
        $.ajax({
            url: '/start_process',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({}),
            success: function(response) {
                console.log('Action processed:', response);
            },
            error: function(error) {
                console.log('Error processing action:', error);
            }
        });
    }

    function Reset() {
        clearInterval(fetchInterval);
        $.ajax({
            url: '/reset',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({}),
            success: function(response) {
                console.log('Reset:', response);
                $('.info_table tbody').html('');
                $('#Start').prop('disabled', false);
                if ($('#Pause').text() === '继续') {
                    $('#Pause').text('暂停'); 
                }
            },
            error: function(error) {
                console.log('Error reseting:', error);
                $('#Start').prop('disabled', false);
            }
        });
        fetchMemoryStatus();
    }

    function Pause() {
        $.ajax({
            url: '/pause',
            type: 'POST',
            contentType: 'application/json',
            success: function(response) {
                console.log('Pause:', response.message);  
            },
            error: function(error) {
                console.log('Error pausing:', error);  
            }
        });
    }

    function change_process_method() {
        $.ajax({
            url: '/conCmd',
            type: 'POST',
            contentType: 'application/json',
            success: function(response) {
                console.log('change_method:', response.message);  
            },
            error: function(error) {
                console.log('Error changing method:', error);  
            }
        });
    }

    function change_single_command() {
        $.ajax({
            url: '/oneCmd',
            type: 'POST',
            contentType: 'application/json',
            success: function(response) {
                console.log('change_method:', response.message);  
            },
            error: function(error) {
                console.log('Error changing method:', error);  
            }
        });
    }
});
