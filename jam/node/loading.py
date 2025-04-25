from pathlib import Path
from tomllib import load
from uuid import UUID, uuid4

from tomlkit import document, table, aot, inline_table, dump

from .render import GraphRenderer
from .node import Graph, Connection, STR_CAST, CAST_STR
from .blocks import BLOCKS, Variable

__all__ = ("read_graph", "write_graph")


def read_graph(pth: Path) -> tuple[Graph, dict[UUID, tuple[float, float]]]:
    with open(pth, "rb") as fp:
        raw_data = load(fp)

    config_table = raw_data["Config"]
    block_table = raw_data["Block"]
    connection_table = raw_data["Connection"]

    variables = {}
    for variable_data in block_table.get("Variables", []):
        data = (
            {
                name: STR_CAST[typ]
                for name, typ in variable_data.get("inputs", {}).items()
            },
            {
                name: STR_CAST[typ]
                for name, typ in variable_data.get("outputs", {}).items()
            },
        )
        variables[UUID(variable_data["uid"])] = data

    graph = Graph(config_table.get("name", ""))
    positions = {}

    for block_data in block_table.get("Data", []):
        typ = BLOCKS[block_data["type"]]

        uid = block_data.get("uid", None)
        if uid is not None:
            uid = UUID(uid)

        if uid in variables:
            block: Variable = typ(block_data.get("name", None), uid)
            config = block_data.get("config", {})
            variable_data = variables[uid]
            for inp, typ in variable_data[0].items():
                block.add_variable(inp, typ, config.get(inp, None), output=False)
            for out, typ in variable_data[1].items():
                block.add_variable(out, typ, config.get(out, None), output=True)
        else:
            block = typ(
                block_data.get("name", None),
                uid,
                **block_data.get("config", {}),
            )

        graph.add_block(block)

        positions[block.uid] = tuple(block_data.get("position", (0.0, 0.0)))

    for connection_data in connection_table.get("Data", []):
        source_uid = UUID(connection_data["source"])
        target_uid = UUID(connection_data["target"])

        source = graph.get_block(source_uid)
        target = graph.get_block(target_uid)

        if source is None or target is None:
            raise KeyError(f"Failed to read graph {graph._name} as it has invalid uids")

        connection_output = connection_data["output"]
        connection_input = connection_data["input"]

        uid = connection_data.get("uid", None)
        if uid is not None:
            uid = UUID(uid)
        else:
            uid = uuid4()

        connection = Connection(
            source, connection_output, target, connection_input, uid
        )
        graph.add_connection(connection)

    if config_table.get("blocks", False):
        graph.lock_blocks()

    if config_table.get("connections", False):
        graph.lock_connections()

    return graph, positions


def write_graph(pth: Path, graph: Graph, renderer: GraphRenderer | None = None):
    toml = document()

    config_table = table()
    block_table = table()
    variables = aot()
    blocks = aot()
    connection_table = table()
    connections = aot()

    config_table["name"] = graph._name
    config_table["blocks"] = graph._blocks_locked
    config_table["connections"] = graph._connections_locked
    toml.add("Config", config_table)

    for block in graph._blocks.values():
        block_subtable = table()
        config_table = inline_table()
        typ = type(block)
        block_subtable["uid"] = block.uid.hex
        block_subtable["name"] = block.name
        block_subtable["type"] = typ.__name__
        config_table.update(block._configuration)
        block_subtable["config"] = config_table
        blocks.append(block_subtable)

        if typ == Variable:
            variable_table = table()
            variable_table["uid"] = block.uid.hex
            input_table = inline_table()
            input_table.update(
                {name: CAST_STR[typ] for name, typ in block.inputs.items()}
            )
            output_table = inline_table()
            output_table.update(
                {name: CAST_STR[typ] for name, typ in block.outputs.items()}
            )
            variable_table["inputs"] = input_table
            variable_table["outputs"] = output_table

            variables.append(variable_table)

        if renderer is not None:
            block_renderer = renderer._blocks[block.uid]
            block_subtable["position"] = block_renderer.bottom_left

    block_table.add("Variables", variables)
    block_table.add("Data", blocks)
    toml.add("Block", block_table)

    for connection in graph._connections.values():
        connection_subtable = table()
        connection_subtable["uid"] = connection.uid.hex
        connection_subtable["source"] = connection.source.uid.hex
        connection_subtable["target"] = connection.target.uid.hex
        connection_subtable["output"] = connection.output
        connection_subtable["input"] = connection.input

        connections.append(connection_subtable)

    connection_table.add("Data", connections)
    toml.add("Connection", connection_table)

    with open(pth, "wt") as fp:
        dump(toml, fp)
