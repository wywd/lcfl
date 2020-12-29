# Look Closer to See Better: Recurrent Attention Convolutional Neural Network for Fine-grained Image Recognition [[paper]](https://openaccess.thecvf.com/content_cvpr_2017/papers/Fu_Look_Closer_to_CVPR_2017_paper.pdf)
###### 作者：Jianlong Fu, Heliang Zheng, Tao Mei  
###### 单位：Microsoft Research, Beijing, China 、 University of Science and Technology of China, Hefei, China  
###### 发表：CVPR 2017

## 1. Abstract
▲ 细粒度图像识别的难点在于**判别性区域定位**和**细粒度特征学习**，现存大部分方法独立解决这两个问题，忽略了区域检测和细粒度特征学习是**相互关联**的，作者提出<font color='red'>循环注意力卷积神经网络(RA-CNN)</font>，该网络以相互增强的方式，在多尺度上**递归**地学习判别性的注意力区域和基于区域的特征表示。  
▲ 每个尺度的学习包括一个<font color='red'>分类子网络</font>和<font color='red'>一个注意力建议子网络</font>(attention proposal sub-network，APN)，APN从完整的图像开始，以之前的预测作为参考，迭代的产生由粗到精产生注意力区域，后一个网络由前一个网络输入图像的注意力区域作为输入。  

▲ 通过<font color='red'>尺度内分类损失</font>和<font color='red'>尺度间排序损失(ranking loss)</font>对所提出的RA-CNN网络进行优化，仅使用**类标签**作为监督信息。  

## 2. Contributions
▲ 针对细粒度图像识别的挑战提出了新颖的循环注意力卷积神经网络，该网络能够以相互强化的方式，准确检测有判别性的区域以及有效学习基于区域的特征表示；  
▲ 提出了成对的排序损失(pairwise ranking loss)来优化注意力建议网络，与只有标签监督的区域定位相比，这种设计能够让网络逐步的定位到判别区域；  
▲ 在CUB Birds, Stanford Dogs, Stanford Cars三个数据集上进行的充分的实验，并且实现了最佳的实验结果  

## 3. Approach

### 3.1 RA-CNN网络结构

![](./fgia_pic/RA-CNN网络结构.jpg ':size=100%')  

### 3.2 注意力建议网络（Attention Proposal Network）

▲ 每个尺度的网络都可以看成是一个**多任务学习**的网络，一个任务是分类，一个任务是定位，即返回注意力建议框的位置。  
▲ 作者提出的APN网络受到区域候选网络(PRN)[[1]][1]的启发，用于定位任务，它由堆叠的两个全连接层组成，因此区域注意力的计算几乎是免费的，最后一个全连接层返回三个定位值，建议框的中心坐标 {$t_x$;$t_y$} 以及半边长 {$t_l$} 。  
$ \left[t_{x}, t_{y}, t_{l}\right]=g\left(\mathbf{W}_{c} * \mathbf{X}\right) $  

一旦注意力区域的位置确定了，将通过**裁剪**、**缩放**注意力区域，使其具有更精细的尺度、更高的分辨率，从而提取出更多细粒度的特征。  

▲ 裁剪过程中，使用一种称为**二维boxcar函数**的变体作为注意力掩码，它是一个连续函数，便于在反向传播中进行优化。  

---
具体操作如下：  

假设原始图像的左上角是像素坐标系的原点，其x轴和y轴分别从左到右和从上到下定义。对注意力区域中的点进行如下参数化：  $tl$表示左上的点，$br$ 表示右下的点：  

$ t_{x(tl)} = t_x-t_l $，$t_{y(tl)} = t_y - t_l$，  
$ t_{x(br)} = t_x+t_l$，$t_{y(br)} = t_y+t_l$.  

然后通过粗糙尺度下的原始图像和注意力掩码间的按位乘法实现剪裁操作，公式如下：  

$ X^{att}=X \odot M(t_x, t_y, t_l) $  

$\odot$表示按位乘法，$X^{att}$表示被裁减的注意力区域，$M(\bullet)$为注意力掩码，具体形式如下：   
$M(\bullet)=[h(x-t_{x(tl)})-h(x-t_{x(br)})] \bullet [h(y-t_{y(tl)})-h(y-t_{y(br)})]$  

其中，$h(x)$是一个指数为$k$的logisitc函数：$ h(x) = 1/{\{1+exp^{-kx}\}} $  

> 当 $k$ 很大时:  
> $x$ 为正时, $h(x)$ 值为1; $x$ 为负时, $h(x)$ 值为0。  
> 当 $k$ 很大时:  
> $x$ 小于 $t_{x(t l)}, t_{x(b r)}, h(x)$ 值为0，进而 $M(\bullet)$ 值为0；  
> $x$ 大于 $t_{x(t l)}, t_{x(b r)}, h(x)$ 值为1，进而 $M(\bullet)$ 值为0。   
> 同理, $y$ 与 $t_{y(t l)}, t_{y(b r)}$ 的关系也具有同样的性质。  
> 因此, 保证了在 $t_{x(t l)}, t_{x(b r)}$ 和 $t_{y(t l)}, t_{y(b r)}$ 限定的范围内, $M(\bullet)$ 值为1。  

---

▲ 通过自适应缩放进一步将区域放大到更大的尺寸，有利于提取出有效的特征表示。本文使用双线性插值算法计算放大的输出$X^{amp}$，该放大的输出是由$X^{att}$最近的四个输入通过线性映射的方式得到的，公式如下：  

$ \mathbf{X}_{(i, j)}^{a m p}=\sum_{\alpha, \beta=0}^{1}|1-\alpha-\{i / \lambda\} \| 1-\beta-\{j / \lambda\}| \mathbf{X}_{(m, n)}^{a t t} $  

其中，$ m=[i / \lambda]+\alpha, n=[j / \lambda]+\beta $。$\lambda$是上采样因子，等于放大后的尺寸除以$t_l$。$[\bullet]$和${\{\bullet\}}$分别是整数和小数部分。  

### 3.3 分类和排序

递归注意力神经网络通过尺度内分类损失和尺度间排序损失进行优化，交替地生成更精确的注意力区域以及学习更细粒度的特征。总的损失函数如下：  

$L(\mathbf{X})=\sum_{s=1}^{3}\left\{L_{c l s}\left(\mathbf{Y}^{(\mathbf{s})}, \mathbf{Y}^{*}\right)\right\}+\sum_{s=1}^{2}\left\{L_{r a n k}\left(p_{t}^{(s)}, p_{t}^{(s+1)}\right)\right\}$   

其中$s$代表每个尺度，$Y^s$和$Y^*$分别为特定尺度下预测的标签向量和ground truth标签向量,$L_{cls}$表示分类损失；两两排序损失$L_{rank}$中的$p_{t}^{(s)}$表示正确类别标签t的预测概率，排序损失公式：  

$L_{\text {rank}}\left(p_{t}^{(s)}, p_{t}^{(s+1)}\right)=\max \left\{0, p_{t}^{(s)}-p_{t}^{(s+1)}+\operatorname{margin}\right\}$   

这个损失函数约束了$p_{t}^{(s+1)}>p_{t}^{(s)}+\operatorname{margin}$，此种设计可以使网络将粗糙尺度的预测作为参考，并且通过强制更细粒度的网络产生更可信的预测来逐渐到达最具分辨力的区域。   

**注意：**$L_{cls}$和$L_{rank}$是**交替训练**的   

### 3.4 多尺度联合表示 

为了利用特征集成的好处，首先将每个网络产生的特征进行归一化，然后将他们拼接在一起，再后接softmax函数作为最终的分类  

### 3.5 训练细节
▲ 使用预训练的VGG网络结构, 三个网络具有相同的网络模型；  
▲  通过搜索原始图像中的区域来选择正方形，在最后的卷积层中具有最高响应值。  
▲  以交替的方式进行训练，首先保持APN的参数不变，来优化每个尺度的softmax损失，然后固定卷积层和分类层的参数不变，使用ranking loss来优化APN；  


## 4. Experiments

### 4.1 Datasets
### 4.2 Experiments on CUB2002011

![](./fgia_pic/RA-CNN-CUB-2011实验结果.jpg ':size=75%')  


## References

[1]:  Girshick R. Fast r-cnn[C]//Proceedings of the IEEE international conference on computer vision. 2015: 1440-1448.
[2]: 







