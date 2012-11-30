function start_arboretum(runtime, elm) {
  var w = 680,
      h = w,
      p = 10,
      max = 192,
      nodes = [{x: w / 2, y: h / 2, size: 1}],
      links = [];

  var force = d3.layout.force()
      .charge(-120)
      .linkDistance(30)
      .nodes(nodes)
      .links(links)
      .size([w, h])
      .on("tick", updatePositions);

  var vis = d3.select(elm).select('.vis').append("svg")
      .attr("width", w + 2 * p)
      .attr("height", h + 2 * p)
    .append("g")
      .attr("transform", "translate(" + [p, p] + ")");

  var link = vis.selectAll("line.link"),
      node = vis.selectAll("circle.node");

  d3.timer(function() {
    var source = nodes[~~(Math.random() * nodes.length)],
        bud = {x: source.x + Math.random() - .5, y: source.y + Math.random() - .5, parent: source, size: 1};
    inflate(bud);
    links.push({source: source, target: bud});
    nodes.push(bud);

    node = node.data(nodes);
    node.enter().append("circle")
        .attr("class", "node")
        .attr("r", 5)
        .attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; })
        .call(force.drag)

    link = link.data(links);
    link.enter().insert("line", "circle")
        .attr("class", "link");

    force.start();

    return nodes.length >= max;
  });

  function inflate(d) {
    while (d = d.parent) d.size++;
  }

  function updatePositions() {
    nodes.forEach(function(o, i) {
      o.x = Math.min(w, Math.max(0, o.x));
      o.y = Math.min(h, Math.max(0, o.y));
    });
    link.style("stroke-width", function(d) { return Math.sqrt(d.target.size); })
        .attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    node.attr("r", function(d) { return 5 + Math.sqrt(d.size) / 2; })
        .attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });
  }
}
