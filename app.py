from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from py3dbp import Packer, Bin, Item

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello from boxlogic"

@app.route('/plan', methods=['POST'])
def plan():
    if request.is_json:
        data = request.get_json()
        container_length = float(data.get('container_length'))
        container_width = float(data.get('container_width'))
        container_height = float(data.get('container_height'))

        bigger_first = data.get('bigger_first', False)
        distribute_items = data.get('distribute_items', False)
        rotation = data.get('rotation', False)
        packing_strategy = data.get('packing_strategy')
        verbose = data.get('verbose', False)

        box_names = data.get('box_name', [])
        box_lengths = data.get('box_length', [])
        box_widths = data.get('box_width', [])
        box_heights = data.get('box_height', [])
        box_weights = data.get('box_weight', [])
        box_quantities = data.get('box_quantity', [])
    else:
        container_length = float(request.form.get('container_length'))
        container_width = float(request.form.get('container_width'))
        container_height = float(request.form.get('container_height'))

        bigger_first = True if request.form.get('bigger_first') else False
        distribute_items = True if request.form.get('distribute_items') else False
        rotation = True if request.form.get('rotation') else False
        packing_strategy = request.form.get('packing_strategy')
        verbose = True if request.form.get('verbose') else False

        box_names = request.form.getlist('box_name[]')
        box_lengths = request.form.getlist('box_length[]')
        box_widths = request.form.getlist('box_width[]')
        box_heights = request.form.getlist('box_height[]')
        box_weights = request.form.getlist('box_weight[]')
        box_quantities = request.form.getlist('box_quantity[]')

    input_summary = []
    error_message = None

    for i in range(len(box_names)):
        if (float(box_lengths[i]) > container_length or
            float(box_widths[i]) > container_width or
            float(box_heights[i]) > container_height):
            error_message = f"Error: Box '{box_names[i]}' is larger than the container."
            if request.is_json:
                return jsonify({"error": error_message}), 400
            else:
                flash(error_message, "danger")
                return render_template(
                    'index.html',
                    results=None,
                    input_summary=input_summary,
                    error_message=error_message
                )
        input_summary.append({
            'name': box_names[i],
            'length': box_lengths[i],
            'width': box_widths[i],
            'height': box_heights[i],
            'quantity': box_quantities[i]
        })

    items_to_pack = []
    for i in range(len(box_names)):
        for _ in range(int(box_quantities[i])):
            items_to_pack.append(Item(
                name=box_names[i],
                width=float(box_widths[i]),
                height=float(box_heights[i]),
                depth=float(box_lengths[i]),
                weight=float(box_weights[i])
            ))

    if packing_strategy == "best_fit":
        items_to_pack.sort(
            key=lambda item: item.width * item.height * item.depth,
            reverse=True
        )

    packed_bins = []
    unpacked_items = items_to_pack

    while unpacked_items:
        packer = Packer()
        bin = Bin(
            name=f"Container-{len(packed_bins) + 1}",
            width=container_width,
            height=container_height,
            depth=container_length,
            max_weight=100000
        )
        packer.add_bin(bin)

        for item in unpacked_items:
            packer.add_item(item)

        packer.pack(
            bigger_first=bigger_first,
            distribute_items=distribute_items,
            number_of_decimals=2
        )

        packed_bins.append(bin)
        unpacked_items = bin.unfitted_items

        if verbose:
            print(f"[DEBUG] {bin.name}: Packed {len(bin.items)} items, {len(unpacked_items)} left.")

    results = []
    for i, bin in enumerate(packed_bins):
        total_volume = bin.width * bin.height * bin.depth
        packed_volume = sum(item.width * item.height * item.depth for item in bin.items)
        utilization = (packed_volume / total_volume) * 100 if total_volume > 0 else 0

        packed_items_data = []
        for item in bin.items:
            item_dims = item.get_dimension()
            packed_items_data.append({
                'name': item.name,
                'position': item.position,
                'dimensions': {
                    'length': float(item_dims[0]),
                    'width': float(item_dims[1]),
                    'height': float(item_dims[2])
                }
            })

        results.append({
            'container_name': f"Container {i + 1}",
            'utilization': f"{utilization:.2f}%",
            'container_dimensions': {
                'length': bin.depth,
                'width': bin.width,
                'height': bin.height
            },
            'packed_items_data': packed_items_data,
        })

    if request.is_json:
        return jsonify({
            "results": results,
            "num_containers": len(packed_bins),
            "input_summary": input_summary,
            "error_message": None
        })
    else:
        return render_template(
            'index.html',
            results=results,
            num_containers=len(packed_bins),
            input_summary=input_summary,
            error_message=None
        )

if __name__ == '__main__':
    app.run(debug=True)
