from typing import List, Optional
from .error import IllegalRuntimeException
# Công cụ dùng để theo dõi trạng thái của khung ngăn xếp khi tạo mã máy cho một phương thức cụ thể.
# Quản lý thông tin của label, stack và biến cục bộ trong quá trình tạo mã máy.
# Vị trí bắt đầu, kết thúc của phạm vi, vòng lặp và chỉ mục biến cục bộ được theo dõi để đảm bảo mã máy chính xác.

# 2 điều quan trọng nhất:
# Muốn sinh mã thì phải đi tìm emitter
# Muốn đụng tới label, local variable array, operation stack -> o.frame
# Khi visit expr thì phải trả về code với type


# -----------------------------
# cách sinh mã cho statement
# bước 1: vẽ flowchart của stmt đó sao cho tất cả các khối nằm trên 1 phương thẳng đúng từ trên xuống
# bước 2: xác định xem trên flowchart có bao nhiêu rẽ nhánh hay điểm nhảy thì sinh bấy nhiêu label
# sinh label bằng cách gọi hàm o.frame.getNewLabel()
#
#
# bước 3: viết mã giả cho từng khối theo phương thẳng đúng từ trên xuống dưới khi gặp rẽ nhánh
# thì xử lý rẽ nhánh trước rồi ngay lặp tức quay lại với trục chính
# bước 4: từ mã giả ở bước 3 viết mã thật


class Frame:
    """
    Frame class to manage method frame information in code generation.
    
    Attributes:
        name (str): Name of the method
        return_type: Return type of the method
        current_label (int): Current label
        curr_op_stack_size (int): Current size of operand stack
        max_op_stack_size (int): Maximum size of operand stack
        curr_index (int): Current index of local variable
        max_index (int): Maximum index used
        start_label (List[int]): Stack containing start labels of scopes
        end_label (List[int]): Stack containing end labels of scopes
        index_local (List[int]): Stack containing local indices of scopes
        con_label (List[int]): Stack containing continue labels of loops
        brk_label (List[int]): Stack containing break labels of loops
    """
    
    def __init__(self, name: str, return_type):
        """
        Initialize Frame.
        
        Args:
            name: Name of the method
            return_type: Return type of the method
        """
        self.name = name
        self.return_type = return_type
        self.current_label = 0
        self.curr_op_stack_size = 0
        self.max_op_stack_size = 0
        self.curr_index = 0
        self.max_index = 0
        self.start_label: List[int] = []
        self.end_label: List[int] = []
        self.index_local: List[int] = []
        self.con_label: List[int] = []
        self.brk_label: List[int] = []

    def get_curr_index(self) -> int:
        """Return current index."""
        return self.curr_index

    def set_curr_index(self, index: int) -> None:
        """
        Set current index.
        
        Args:
            index: New index
        """
        self.curr_index = index

    def get_new_label(self) -> int:
        """
        Return a new label in the method.
        
        Returns:
            An integer representing the label.
        """
        tmp = self.current_label
        self.current_label = self.current_label + 1
        return tmp

    def push(self) -> None:
        """
        Simulate an instruction that pushes a value onto operand stack.
        """
        self.curr_op_stack_size = self.curr_op_stack_size + 1
        if self.max_op_stack_size < self.curr_op_stack_size:
            self.max_op_stack_size = self.curr_op_stack_size

    def pop(self) -> None:
        """
        Simulate an instruction that pops a value out of operand stack.
        
        Raises:
            IllegalRuntimeException: When stack is empty
        """
        self.curr_op_stack_size = self.curr_op_stack_size - 1
        if self.curr_op_stack_size < 0:
            raise IllegalRuntimeException("Pop empty stack")

    def get_stack_size(self) -> int:
        """Return current stack size."""
        return self.curr_op_stack_size

    def get_max_op_stack_size(self) -> int:
        """
        Return the maximum size of the operand stack that the method needs to use.
        
        Returns:
            An integer representing the maximum stack size
        """
        return self.max_op_stack_size

    def check_op_stack(self) -> None:
        """
        Check if the operand stack is empty or not.
        
        Raises:
            IllegalRuntimeException: If the operand stack is not empty
        """
        if self.curr_op_stack_size != 0:
            raise IllegalRuntimeException("Stack not empty")

    def enter_scope(self, is_proc: bool) -> None:
        """
        Invoked when parsing into a new scope inside a method.
        
        This method creates 2 new labels that represent the starting and ending
        points of the scope. These labels are pushed onto corresponding stacks
        and can be retrieved by get_start_label() and get_end_label().
        In addition, this method also saves the current index of local variable.
        
        Args:
            is_proc: Boolean indicating whether this is a procedure
        """
        start = self.get_new_label()
        end = self.get_new_label()
        self.start_label.append(start)
        self.end_label.append(end)
        self.index_local.append(self.curr_index)
        if is_proc:
            self.max_op_stack_size = 0
            self.max_index = 0

    def exit_scope(self) -> None:
        """
        Invoked when parsing out of a scope in a method.
        
        This method will pop the starting and ending labels of this scope
        and restore the current index.
        
        Raises:
            IllegalRuntimeException: When there is an error exiting scope
        """
        if not self.start_label or not self.end_label or not self.index_local:
            raise IllegalRuntimeException("Error when exit scope")
        self.start_label.pop()
        self.end_label.pop()
        self.curr_index = self.index_local.pop()

    def get_start_label(self) -> int:
        """
        Return the starting label of the current scope.
        
        Returns:
            An integer representing the starting label
            
        Raises:
            IllegalRuntimeException: When there is no start label
        """
        if not self.start_label:
            raise IllegalRuntimeException("None start label")
        return self.start_label[-1]

    def get_end_label(self) -> int:
        """
        Return the ending label of the current scope.
        
        Returns:
            An integer representing the ending label
            
        Raises:
            IllegalRuntimeException: When there is no end label
        """
        if not self.end_label:
            raise IllegalRuntimeException("None end label")
        return self.end_label[-1]

    def get_new_index(self) -> int:
        """
        Return a new index for a local variable declared in a scope.
        
        Returns:
            An integer representing the index of the local variable
        """
        tmp = self.curr_index
        self.curr_index = self.curr_index + 1
        if self.curr_index > self.max_index:
            self.max_index = self.curr_index
        return tmp

    def get_max_index(self) -> int:
        """
        Return the maximum index used in generating code for the current method.
        
        Returns:
            An integer representing the maximum index
        """
        return self.max_index

    def enter_loop(self) -> None:
        """
        Invoked when parsing into a loop statement.
        
        This method creates 2 new labels that represent the starting and ending
        labels of the loop. These labels are pushed onto corresponding stacks
        and can be retrieved by get_continue_label() and get_break_label().
        """
        con = self.get_new_label()
        brk = self.get_new_label()
        self.con_label.append(con)
        self.brk_label.append(brk)

    def exit_loop(self) -> None:
        """
        Invoked when parsing out of a loop statement.
        
        This method will take 2 labels representing the starting and ending
        labels of the current loop out of its stacks.
        
        Raises:
            IllegalRuntimeException: When there is an error exiting loop
        """
        if not self.con_label or not self.brk_label:
            raise IllegalRuntimeException("Error when exit loop")
        self.con_label.pop()
        self.brk_label.pop()

    def get_continue_label(self) -> int:
        """
        Return the label of the innermost enclosing loop to which continue
        statement would jump.
        
        Returns:
            An integer representing the continue label
            
        Raises:
            IllegalRuntimeException: When there is no continue label
        """
        if not self.con_label:
            raise IllegalRuntimeException("None continue label")
        return self.con_label[-1]

    def get_break_label(self) -> int:
        """
        Return the label of the innermost enclosing loop to which break
        statement would jump.
        
        Returns:
            An integer representing the break label
            
        Raises:
            IllegalRuntimeException: When there is no break label
        """
        if not self.brk_label:
            raise IllegalRuntimeException("None break label")
        return self.brk_label[-1]

