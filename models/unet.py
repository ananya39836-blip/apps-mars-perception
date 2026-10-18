"""Small U-Net semantic segmentation network skeleton in PyTorch.
Part 3 Appendix L - Tasks 11 & 12.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


def block(i, o):
    return nn.Sequential(
        nn.Conv2d(i, o, 3, padding=1),
        nn.BatchNorm2d(o),
        nn.ReLU(inplace=True),
        nn.Conv2d(o, o, 3, padding=1),
        nn.BatchNorm2d(o),
        nn.ReLU(inplace=True)
    )


class SmallUNet(nn.Module):
    def __init__(self, in_ch=4, n_cls=4, w=16, p_drop=0.1):
        super().__init__()
        self.e1 = block(in_ch, w)
        self.e2 = block(w, 2 * w)
        self.e3 = block(2 * w, 4 * w)
        self.pool = nn.MaxPool2d(2)
        self.up2 = nn.ConvTranspose2d(4 * w, 2 * w, 2, stride=2)
        self.d2 = block(4 * w, 2 * w)
        self.up1 = nn.ConvTranspose2d(2 * w, w, 2, stride=2)
        self.d1 = block(2 * w, w)
        self.drop = nn.Dropout2d(p_drop)
        self.out = nn.Conv2d(w, n_cls, 1)

    def forward(self, x):
        a = self.e1(x)
        b = self.e2(self.pool(a))
        c = self.e3(self.pool(b))
        b2 = self.d2(torch.cat([self.up2(c), b], 1))
        a2 = self.d1(torch.cat([self.up1(b2), a], 1))
        return self.out(self.drop(a2))


def dice_loss(logits, y, n_cls=4, eps=1e-6):
    """Multi-class Dice loss on known classes."""
    p = F.softmax(logits, 1)
    # Mask out ignore index if present
    valid = (y < n_cls)
    y_clamped = torch.where(valid, y, torch.zeros_like(y))
    oh = F.one_hot(y_clamped, n_cls).permute(0, 3, 1, 2).float()
    
    # zero-out one-hot on invalid pixels
    oh = oh * valid.unsqueeze(1).float()
    
    inter = (p * oh).sum((0, 2, 3))
    den = (p * valid.unsqueeze(1).float()).sum((0, 2, 3)) + oh.sum((0, 2, 3))
    return 1.0 - ((2.0 * inter + eps) / (den + eps)).mean()


def loss_fn(logits, y, class_w=None, dice_w=0.2):
    """Hybrid Cross-Entropy with class weights + Dice Loss, ignoring novel class (index 4)."""
    ce = F.cross_entropy(logits, y, weight=class_w, ignore_index=4)
    dl = dice_loss(logits, y, n_cls=4)
    return ce + dice_w * dl


def prepare(img, depth):
    """img: HxWx3 float, depth: HxW float -> 1x4xHxW tensor, depth centred on its median."""
    d = depth - torch.as_tensor(depth).median()
    x = torch.cat([torch.as_tensor(img).permute(2, 0, 1), d.unsqueeze(0)], 0)
    return x.unsqueeze(0).float()
