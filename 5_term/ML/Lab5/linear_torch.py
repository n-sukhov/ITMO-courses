import torch 


class TorchMLP(torch.nn.Module):
    def __init__(
            self, 
            input_dim: int,
            hidden_dim: int,
            output_dim: int,
    ):
        super().__init__()
        self.layer1 = torch.nn.Linear(input_dim, hidden_dim)
        self.bn1 = torch.nn.BatchNorm1d(hidden_dim)
        self.relu = torch.nn.ReLU()
        self.dropout1 = torch.nn.Dropout(p=0.5)
        self.layer2 = torch.nn.Linear(hidden_dim, output_dim)

    def forward(self, x:torch.Tensor) -> torch.Tensor:
        x = self.layer1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.dropout1(x)
        x = self.layer2(x)
        return x
    
class ClassificationLoss(torch.nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, predictions: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        log_probs = torch.log_softmax(predictions, dim=1)
        loss = -torch.mean(log_probs[torch.arange(predictions.shape[0]), targets])
        return loss