from flask import Flask, render_template, request
from py3dbp import Packer, Bin, Item

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Container dimensions
        container_length = float(request.form.get('container_length'))
        container_width = float(request.form.get('container_width'))
        container_height = float(request.form.get('container_height'))

        # Box data
        box_names = request.form.getlist('box_name[]')
        box_lengths = request.form.getlist('box_length[]')
        box_widths = request.form.getlist('box_width[]')
        box_heights = request.form.getlist('box_height[]')
        box_weights = request.form.getlist('box_weight[]')
        box_quantities = request.form.getlist('box_quantity[]')
        
        # Create a summary of the input boxes for display
        input_summary = []
        for i in range(len(box_names)):
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

            packer.pack()
            packed_bins.append(bin)
            unpacked_items = bin.unfitted_items
        
        results = []
        for i, bin in enumerate(packed_bins):
            total_volume = bin.width * bin.height * bin.depth
            packed_volume = sum(item.width * item.height * item.depth for item in bin.items)
            utilization = (packed_volume / total_volume) * 100 if total_volume > 0 else 0
            
            packed_items_data = []
            for item in bin.items:
                # py3dbp returns dimensions as (depth, width, height)
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

        return render_template(
            'index.html', 
            results=results, 
            num_containers=len(packed_bins), 
            input_summary=input_summary
        )

    return render_template('index.html', results=None)

if __name__ == '__main__':
    app.run(debug=True)