from uuid import UUID, uuid4
from pathlib import Path
from tomllib import load as load_toml
from tomlkit import document, table, inline_table, aot, dump as dump_toml

from station.node.graph import (
    Graph,
    Block,
    Connection,
    BlockType,
    OperationValue,
    TestCase,
    BLOCK_CAST,
    STR_CAST,
    _variable,
)
from station.node import blocks as block_impl
from station.puzzle import Puzzle
from station.gui.graph import BlockElement, ConnectionElement, TempValueElement
from station.gui.core import Gui


class GraphController:

    def __init__(
        self,
        gui: Gui,
        name: str = "graph",
        available: tuple[BlockType, ...] | None = None,
        sandbox: bool = False,
        cases: tuple[TestCase, ...] | None = None,
        input_block: UUID | None = None,
        output_block: UUID | None = None,
    ):
        self._graph: Graph = Graph(
            name, available, sandbox, cases, input_block, output_block
        )
        self._gui = gui

        self._block_elements: dict[UUID, BlockElement] = {}
        self._connection_elements: dict[UUID, ConnectionElement] = {}

        self._temp_elements: dict[UUID, TempValueElement] = {}

    @property
    def graph(self) -> Graph:
        return self._graph

    @property
    def gui(self) -> Gui:
        return self.gui

    @property
    def blocks(self) -> tuple[BlockElement, ...]:
        return tuple(self._block_elements.values())

    @property
    def connections(self) -> tuple[ConnectionElement, ...]:
        return tuple(self._connection_elements.values())

    @property
    def temporary(self) -> tuple[TempValueElement, ...]:
        return tuple(self._temp_elements.values())

    def has_block(self, uid: UUID) -> bool:
        return uid in self._block_elements

    def has_connection(self, uid: UUID) -> bool:
        return uid in self._connection_elements

    def has_temp(self, uid: UUID) -> bool:
        return uid in self._temp_elements

    def get_block(self, uid: UUID) -> BlockElement:
        if uid not in self._block_elements:
            raise KeyError(f"No block with uid {uid}")
        return self._block_elements[uid]

    def get_connection(self, uid: UUID) -> ConnectionElement:
        if uid not in self._connection_elements:
            raise KeyError(f"No connection with uid {uid}")

        return self._connection_elements[uid]

    def get_temp(self, uid: UUID) -> TempValueElement:
        if uid not in self._temp_elements:
            raise KeyError(f"No temp value with the uid {uid}")

        return self._temp_elements[uid]

    def add_block(self, block: BlockElement, add_temp: bool = True) -> None:
        self._graph.add_block(block.block)
        self._gui.add_element(block)
        self._block_elements[block.uid] = block

        if not add_temp:
            return

        for inp, connection in block.block.inputs.items():
            if connection is not None:
                continue
            self.create_temporary(block, inp)

    def remove_block(self, block: BlockElement) -> None:
        for connection in block._input_connections.values():
            if connection is None:
                continue
            elif connection.uid in self._temp_elements:
                self.remove_temporary(connection)
            else:
                self._unlink_connection(connection)

        for output in block._output_connections.values():
            for connection in output:
                self._unlink_connection(connection)

        self._gui.remove_element(block)
        self._graph.remove_block(block.block)
        self._block_elements.pop(block.uid)

    def add_connection(self, connection: ConnectionElement) -> None:
        self._link_connection(connection)
        self._graph.add_connection(connection.connection)

    def remove_connection(self, connection: ConnectionElement) -> None:
        self._unlink_connection(connection)
        self._graph.remove_connection(connection.connection)

        target = self.get_block(connection.connection.target)
        self.create_temporary(target, connection.connection.input)

    def _link_connection(self, connection: ConnectionElement) -> None:
        target = self.get_block(connection.connection.target)
        inp = target._input_connections[connection.connection.input]
        if inp is not None:
            if inp.uid in self._connection_elements:
                self._unlink_connection(inp)
            elif inp.uid in self._temp_elements:
                self.remove_temporary(inp)
        target._input_connections[connection.connection.input] = connection
        source = self.get_block(connection.connection.source)
        source._output_connections[connection.connection.output].append(connection)

        target.get_input(connection.connection.input).active = True
        source.get_output(connection.connection.output).active = True

        self._connection_elements[connection.uid] = connection
        self._gui.add_element(connection)

    def _unlink_connection(self, connection: ConnectionElement) -> None:
        target = self.get_block(connection.connection.target)
        source = self.get_block(connection.connection.source)

        target._input_connections[connection.connection.input] = None
        source._output_connections[connection.connection.output].remove(connection)

        target.get_input(connection.connection.input).active = False
        if not source._output_connections[connection.connection.output]:
            source.get_output(connection.connection.output).active = False

        self._connection_elements.pop(connection.uid)
        self._gui.remove_element(connection)

    def create_temporary(
        self, block: BlockElement, inp: str, value: OperationValue | None = None
    ) -> None:
        connection = block._input_connections[inp]
        if connection is not None:
            return

        block_typ = block.block.type
        temp_type = BLOCK_CAST[block_typ.inputs[inp]._typ]
        temp_block = Block(temp_type, uid=None)
        if value is not None:
            temp_block.config["value"] = value
        elif inp in block_typ.defaults:
            temp_block.config["value"] = block_typ.defaults[inp]
        temp_connection = Connection(temp_block.uid, "value", block.uid, inp)
        element = TempValueElement(temp_block, temp_connection)
        element.update_end(block.get_input(inp).link_pos)

        self._gui.add_element(element)
        self._graph.add_block(temp_block)
        self._graph.add_connection(temp_connection)

        block._input_connections[inp] = element
        block.get_input(inp).active = True
        self._temp_elements[temp_block.uid] = element

    def remove_temporary(self, temp: TempValueElement) -> None:
        self._gui.remove_element(temp)
        self._graph.remove_block(temp.block)
        self._temp_elements.pop(temp.uid)


def read_graph(path: Path, gui: Gui, sandbox: bool = False) -> GraphController:
    with open(path, "rb") as fp:
        raw_data = load_toml(fp)

    config_table = raw_data["Config"]
    block_table = raw_data.get("Block", {})
    connection_table = raw_data.get("Connection", {})

    controller = GraphController(
        gui, config_table.get("name", "graph"), sandbox=sandbox
    )

    variable_types: dict[str, BlockType] = {}
    for variable in block_table.get("Variable", []):
        inputs = {name: STR_CAST[typ] for name, typ in variable["inputs"].items()}
        outputs = {name: STR_CAST[typ] for name, typ in variable["outputs"].items()}
        config = outputs.copy()

        name = variable["name"]
        variable_types[name] = BlockType(name, _variable, inputs, outputs, config)

    for block in block_table.get("Data", []):
        uid_str: str | None = block.get("uid", None)
        if uid_str is not None:
            uid = UUID(uid_str)
        else:
            uid = uuid4()

        type_str: str = block["type"]
        if type_str in variable_types:
            block_type = variable_types[type_str]
        else:
            block_type = BlockType.__definitions__[type_str]

        config = {
            name: block_type.config[name](value)
            for name, value in block.get("config", {}).items()
        }

        graph_block = Block(block_type, uid, *config)
        element = BlockElement(graph_block)
        element.update_position(block.get("position", (0.0, 0.0)))
        controller.add_block(element, add_temp=False)

    for connection in connection_table.get("Data", []):
        uid_str: str | None = connection.get("uid", None)
        if uid_str is not None:
            uid = UUID(uid_str)
        else:
            uid = uuid4()

        source_ = UUID(connection["source"])
        output_ = connection["output"]
        target_ = UUID(connection["target"])
        input_ = connection["input"]

        start = controller.get_block(source_).get_output(output_).link_pos
        end = controller.get_block(target_).get_input(input_).link_pos

        links = connection.get("links", ())

        graph_connection = Connection(
            source_,
            output_,
            target_,
            input_,
            uid,
        )
        element = ConnectionElement(graph_connection, start, end, links=links)
        controller.add_connection(element)

    for block in controller.blocks:
        for inp in block.block.type.inputs:
            if block._input_connections[inp] is not None:
                continue
            controller.create_temporary(block, inp)

    return controller


def read_graph_from_level(puzzle: Puzzle, gui: Gui) -> GraphController:
    path = puzzle.source_graph
    if path is None:
        input_block = Block(puzzle.input_type)
        input_element = BlockElement(input_block)
        input_element.update_position((50.0, 300.0))
        output_block = Block(puzzle.output_type)
        output_element = BlockElement(output_block)
        output_element.update_position((750.0, 300.0))

        controller = GraphController(
            gui,
            puzzle.title,
            puzzle.available,
            False,
            puzzle.tests,
            input_block.uid,
            output_block.uid,
        )

        controller.add_block(input_element)
        controller.add_block(output_element)

        return controller
    controller = read_graph(path, gui)
    graph = controller.graph

    graph._name = puzzle.title
    if puzzle.available is not None:
        graph.available = puzzle.available
    graph.cases = puzzle.tests

    input_uid = output_uid = None
    for block in graph.blocks:
        if input_uid is None and block.type.name == puzzle.input_type.name:
            input_uid = block.uid
        if output_uid is None and block.type.name == puzzle.output_type.name:
            output_uid = block.uid

        if input_uid and output_uid:
            break

    if input_uid is None:
        raise ValueError(
            f"Puzzle {puzzle.name}, and its graph are missing an input block"
        )
    if output_uid is None:
        raise ValueError(
            f"Puzzle {puzzle.name}, and its graph are missing an output block"
        )

    graph.input_uid = input_uid
    graph.output_uid = output_uid

    return controller


def write_graph(controller: GraphController, path: Path) -> None:
    toml = document()

    graph = controller.graph

    config_table = table()
    block_table = table()
    variables = aot()
    blocks = aot()
    connection_table = table()
    connections = aot()

    config_table["name"] = controller.graph.name
    toml.add("Config", config_table)
    for block in graph.blocks:
        subtable = table()
        config = inline_table()

        subtable["uid"] = block.uid.hex
        subtable["type"] = block.type.name
        config.update(  # type: ignore -- unknownMemberType
            {name: typ.value for name, typ in block.config.items()}
        )
        subtable["config"] = config

        if controller.has_block(block.uid):
            element = controller.get_block(block.uid)
            subtable["position"] = element.left, element.bottom
        else:
            element = controller.get_temp(block.uid)
            subtable["position"] = element.left, element.bottom

        blocks.append(subtable)  # type: ignore -- unknownMemberType

        if block.type.exclusive:
            type_table = table()
            input_table = inline_table()
            input_table.update(  # type: ignore -- unknownMemberType
                {
                    name: str(typ._typ.__name__)
                    for name, typ in block.type.inputs.items()
                }
            )
            output_table = inline_table()
            output_table.update(  # type: ignore -- unknownMemberType
                {
                    name: str(typ._typ.__name__)
                    for name, typ in block.type.outputs.items()
                }
            )
            type_table["name"] = block.type.name
            type_table["inputs"] = input_table
            type_table["outputs"] = output_table
            variables.append(type_table)  # type: ignore -- unknownMemberType

    block_table["Variables"] = variables
    block_table["Data"] = blocks
    toml["Block"] = block_table

    for connection in graph.connections:
        subtable = table()
        subtable["uid"] = connection.uid.hex
        subtable["source"] = connection.source.hex
        subtable["output"] = connection.output
        subtable["target"] = connection.target.hex
        subtable["input"] = connection.input

        if controller.has_connection(connection.uid):
            element = controller.get_connection(connection.uid)
            if len(element._links) > 2:
                subtable["links"] = element._links[1:-1]

        connections.append(subtable)  # type: ignore -- unknownMemberType
    connection_table["Data"] = connections
    toml["Connection"] = connection_table

    with path.open(mode="w", encoding="utf-8") as fp:
        dump_toml(toml, fp)


def write_graph_from_level(
    controller: GraphController, puzzle: Puzzle, path: Path
) -> None:
    toml = document()

    graph = controller.graph

    config_table = table()
    block_table = table()
    variables = aot()
    blocks = aot()
    connection_table = table()
    connections = aot()

    config_table["name"] = puzzle.title
    toml.add("Config", config_table)
    for block in graph.blocks:
        subtable = table()
        config = inline_table()

        subtable["uid"] = block.uid.hex
        subtable["type"] = block.type.name
        config.update(  # type: ignore -- unknownMemberType
            {name: typ.value for name, typ in block.config.items()}
        )
        subtable["config"] = config

        if controller.has_block(block.uid):
            element = controller.get_block(block.uid)
            subtable["position"] = element.left, element.bottom
        else:
            element = controller.get_temp(block.uid)
            subtable["position"] = element.left, element.bottom

        blocks.append(subtable)  # type: ignore -- unknownMemberType

        if block.type.exclusive:
            type_table = table()
            input_table = inline_table()
            input_table.update(  # type: ignore -- unknownMemberType
                {
                    name: str(typ._typ.__name__)
                    for name, typ in block.type.inputs.items()
                }
            )
            output_table = inline_table()
            output_table.update(  # type: ignore -- unknownMemberType
                {
                    name: str(typ._typ.__name__)
                    for name, typ in block.type.outputs.items()
                }
            )
            type_table["name"] = block.type.name
            type_table["inputs"] = input_table
            type_table["outputs"] = output_table
            variables.append(type_table)  # type: ignore -- unknownMemberType

    block_table["Variables"] = variables
    block_table["Data"] = blocks
    toml["Block"] = block_table

    for connection in graph.connections:
        subtable = table()
        subtable["uid"] = connection.uid.hex
        subtable["source"] = connection.source.hex
        subtable["output"] = connection.output
        subtable["target"] = connection.target.hex
        subtable["input"] = connection.input

        if controller.has_connection(connection.uid):
            element = controller.get_connection(connection.uid)
            if len(element._links) > 2:
                subtable["links"] = element._links[1:-1]

        connections.append(subtable)  # type: ignore -- unknownMemberType
    connection_table["Data"] = connections
    toml["Connection"] = connection_table

    with path.open(mode="w", encoding="utf-8") as fp:
        dump_toml(toml, fp)
