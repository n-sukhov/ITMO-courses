import torch


class LinearLayerFunction(torch.autograd.Function):
    @staticmethod
    def forward(
        ctx,
        input: torch.Tensor,
        weight: torch.Tensor,
        bias: torch.Tensor | None
    ) -> torch.Tensor:
        ctx.save_for_backward(input, weight, bias)
        output = input @ weight.T
        if bias is not None:
            output += bias
        return output

    @staticmethod
    def backward(
        ctx,
        grad_output: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor | None]:
        input, weight, bias = ctx.saved_tensors
        grad_input = grad_output @ weight
        grad_weight = grad_output.T @ input
        if bias is not None:
            grad_bias = grad_output.sum(0)
        else:
            grad_bias = None
        return grad_input, grad_weight, grad_bias


class LinearLayerModule(torch.nn.Module):
    def __init__(
            self,
            in_features: int,
            out_features: int,
            bias: bool = True
    ):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = torch.nn.Parameter(torch.randn(out_features, in_features))
        if bias:
            self.bias = torch.nn.Parameter(torch.zeros(out_features))
        else:
            self.bias = None
        self.__init_weights()

    def __init_weights(self):
        torch.nn.init.kaiming_uniform_(self.weight, a=5**0.5)
        if self.bias is not None:
            fan_in, _ = torch.nn.init._calculate_fan_in_and_fan_out(self.weight)
            bound = 1 / fan_in**0.5
            torch.nn.init.uniform_(self.bias, -bound, bound)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return LinearLayerFunction.apply(input, self.weight, self.bias)


class CustomMLP(torch.nn.Module):
    def __init__(
            self, 
            input_dim: int,
            hidden_dim: int,
            output_dim: int,
    ):
        super().__init__()
        self.layer1 = LinearLayerModule(input_dim, hidden_dim)
        self.bn1 = torch.nn.BatchNorm1d(hidden_dim)
        self.relu = torch.nn.ReLU()
        self.dropout1 = torch.nn.Dropout(p=0.5)
        self.layer2 = LinearLayerModule(hidden_dim, output_dim)


    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.layer1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.dropout1(x)
        x = self.layer2(x)
        return x