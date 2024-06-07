from flask import Flask, render_template, request, jsonify
from threading import Thread
import blocks_and_pages

app = Flask(__name__, static_folder='static')
memory = blocks_and_pages.memManager(method='FIFO')  

@app.route('/')
def index():
    return render_template('index.html')

#确认算法
@app.route('/set_algorithm', methods=['POST'])
def set_algorithm():
    global memory
    try:
        data = request.get_json() 
        algorithm = data['algorithm']
        memory.change_method(method=algorithm)
        return jsonify({'message': 'Algorithm set to {}'.format(algorithm)})
    except Exception as e:
        print("Error: ", e)
        return jsonify({'error': str(e)}), 500

#获取当前状态
@app.route('/get_memory_status')
def get_memory_status():
    if memory is not None:
        memory_blocks = memory.get_current_status()
        extra_stats = memory.cal_params()
        swap_info=memory.get_swap_info()
        response_data = {
            'memory_blocks': memory_blocks,
            'extra_stats': extra_stats,
            'swap_info':swap_info
        }
        return jsonify(response_data)
    else:
        return jsonify({'error': 'Memory manager is not initialized'}), 400
    
#开始运行
@app.route('/start_process', methods=['POST'])
def start_process():
    thread = Thread(target=memory.startProcessing)
    thread.start()
    return jsonify({'message': 'Process started'})

#重置
@app.route('/reset', methods=['POST'])
def reset():
    global memory
    memory.reset()
    memory = blocks_and_pages.memManager(method='FIFO')  
    return jsonify({'message': 'Process cleared'})

#获取统计结果
@app.route('/get_params')
def get_params():
    params = memory.cal_params()  
    return jsonify(params)

#暂停
@app.route('/pause', methods=['POST'])
def pause():
    memory.change_pause_status()
    return jsonify({'message': 'Process paused'})

#单步执行
@app.route('/conCmd', methods=['POST'])
def switch_process_method():
    memory.change_process_method()
    return jsonify({'message': 'Process switched'})

#连续执行
@app.route('/oneCmd', methods=['POST'])
def switch_single_command():
    memory.change_single_status()
    return jsonify({'message': 'Single command status changed'})

if __name__ == '__main__':
    app.run(debug=True)
