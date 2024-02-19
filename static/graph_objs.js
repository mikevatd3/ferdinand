const SELECTED_COLOR = "#edce32";
const PARENT_COLOR = "#7185eb";
const CHILD_COLOR = "#61c079";
const PHRASE_COLOR = "lightcoral";
const SENTENCE_COLOR = "#35b5c0";

const shortenSentence = (text) => text.length > 25 ? text.slice(0, 22) + "..." : text;

class Label {
    constructor(id, words) {
        this.id = "l-" + id;
        this.words = words;
    }
    handle(event) {
        switch(event) {
            case "mouseover":
                d3.select(`#${this.id}`)
                  .text(this.words)
                  .style("font-size", "larger")
                  .attr("display", "inline")
                break;

            case "indirectOver":
                d3.select(`#${this.id}`)
                  .text(shortenSentence(this.words))
                  .attr("display", "inline")
                break;

            case "mouseout":
                d3.select(`#${this.id}`)
                  .style("font-size", "medium")
                  .attr("display", "none")
                break;
        }
    }
}

class Sentence {
    constructor(id, words) {
        this.id = id;
        this.label = new Label(id, words);
        this.parentLink = null;
        this.parent = null;
        this.childLinks = [];
        this.children = [];
        this.related = [];
    }
    handle(event) {
        switch (event) {
            case "mouseover":
                // First message the event out to linked objects
                this.label.handle("mouseover");
                if (this.parent) {this.parent.handle("parentOver")};
                this.children.forEach(child => child.handle("childOver"));
                this.childLinks.forEach(child =>  child.handle("childLinkOver"));

                // Then handle the d3 stuff on the object itself
                d3.select(`#${this.id}`)
                  .attr("class", "selected_node")
                break;

            case "parentOver":
                this.label.handle("indirectOver");
                d3.select(`#${this.id}`)
                  .attr("class", "parent_node")
                break;

            case "childOver":
                this.label.handle("indirectOver");
                d3.select(`#${this.id}`)
                  .attr("class", "child_node")
                break;

            case "relatedOver":
                break;
            
            case "mouseout":
                if (this.parent) {this.parent.handle("parentOut")};
                this.children.forEach(child => child.handle("childOut"));
                // don't break!

            default:
                this.label.handle("mouseout");
                d3.select(`#${this.id}`)
                  .attr("class", "sentence_node")
                break;

        }
    }
}

class Phrase {
    constructor(id, words) {
        this.id = id;
        this.label = new Label(id, words);
        this.context = null;
        this.contextLink = null;
        this.definition = null;
        this.definitionLink = null;
        this.related = [];
    }
    handle(event) {
        switch (event) {
            case "mouseover":
                this.label.handle("mouseover");
                if (this.context) {this.context.handle("parentOver")};
                if (this.definition) {this.definition.handle("childOver")};

                d3.select(`#${this.id}`)
                  .attr("class", "selected_node")
                break;

            case "parentOver":
                this.label.handle("indirectOver")
                d3.select(`#${this.id}`)
                  .attr("class", "parent_node")
                break;

            case "childOver":
                this.label.handle("indirectOver")
                d3.select(`#${this.id}`)
                  .attr("class", "child_node")
                break;

            case "relatedOver":
                break;

            default:
                this.label.handle("mouseout")
                if (this.context) {this.context.handle("parentOut")};
                if (this.definition) {this.definition.handle("childOut")};

                d3.select(`#${this.id}`)
                  .attr("class", "phrase_node")
        }
    }
}


function buildNode(node) {
    switch (node.type) {
        case 'phrase':
            return new Phrase(
                node.id,
                node.words,
            )
        case 'sentence':
            return new Sentence(
                node.id,
                node.words,
            )
    }
}


class Link {
    constructor(id) {
        this.id = id;
    }
    handle(message) {
        switch (message) {
            default:
                console.log(this.id);
                d3.select(`#${this.id}`)
                  .attr("stroke", "blue")
                  .attr("stroke-width", 3)
        }
    }
}

function buildLink(edge) {
    return new Link(
        `l-${edge.source}-${edge.target}`
    );
}

function makeConnections(edge, comsNodes, comsLinks) {
    source = comsNodes[edge.source];
    target = comsNodes[edge.target];
    link = comsLinks[`l-${edge.source}-${edge.target}`];

    switch (source.constructor) { // 'constructor' is aparently how to get the name of user-defined objects
        case Sentence:
            // Sentence links
            source.children.push(target);
            source.childLinks.push(link);

            // Phrase links
            target.context = source;
            target.contextLink = link;
            break;
        case Phrase:
            // Phrase links
            source.definition = target;
            source.definitionLink = link;

            // Sentence links
            target.parent = source;
            target.parentLink = link;
            break;
    }
};


function buildComsSystem(graph) {
    let comsNodes = {};
    let comsLinks = {};
    graph.nodes.forEach((node) => comsNodes[node.id] = buildNode(node));
    graph.edges.forEach((edge) => comsLinks[`l-${edge.source}-${edge.target}`] = buildLink(edge));
    graph.edges.forEach((edge) => makeConnections(edge, comsNodes, comsLinks));
    
    return comsNodes;
}
