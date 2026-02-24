# Dungeon Queue: Minikube + Kubernetes + Ansible ile Oyunlaştırılmış DevOps Demo

Bu proje artık sadece "task kuyruğu" örneği değil; bir **oyun senaryosu** içeriyor:

> Oyuncular `gateway` API'sine aksiyon gönderir (`kill_monster`, `find_treasure` gibi).  
> `processor` bu event'leri Redis kuyruğundan tüketir, puanı hesaplar ve skor tablosunu günceller.

Amaç: **event-driven microservice mimarisini**, **Kubernetes dağıtımını** ve **Ansible ile versiyon kontrollü rollout** yaklaşımını gerçek bir kullanım hikayesiyle göstermek.

## Hikâye / İş değeri

Bu kurgu; oyun back-end'i, kampanya puan sistemi, kullanıcı aktivite skorlama gibi gerçek dünyadaki asenkron işleme problemlerinin küçük bir modelidir.

- API katmanı (gateway) sadece istek alır ve kuyruğa yazar.
- Worker katmanı (processor) işi arkada işler.
- Redis hem kuyruk hem skor saklama rolü oynar.
- Ansible ile image tag yönetimi merkezileştirilir.

## Mimari

- `gateway`:
  - `POST /play` -> event'i Redis listesine ekler.
  - `GET /score/<player>` -> oyuncu puanını döner.
  - `GET /leaderboard` -> ilk 10 oyuncuyu döner.
- `processor`:
  - Redis kuyruğundan event tüketir.
  - Aksiyona göre puan hesaplar.
  - Skoru Redis hash'te günceller.
- `redis`:
  - Queue key: `game-events`
  - Scoreboard key: `dungeon:scoreboard`

## Klasör Yapısı

- `services/gateway`: Flask API
- `services/processor`: Event worker
- `k8s/templates`: Jinja2 Kubernetes manifest şablonları
- `ansible`: Deploy/destroy ve versiyon değişkenleri

## Ön Gereksinimler

- Docker
- Minikube
- kubectl
- Ansible

## 1) Minikube başlat

```bash
minikube start --cpus=4 --memory=8192
```

Minikube içi Docker daemon kullan:

```bash
eval $(minikube docker-env)
```

## 2) İmajları build et

```bash
docker build -t demo/gateway:v0.1.0 ./services/gateway
docker build -t demo/processor:v0.1.0 ./services/processor
```

## 3) Ansible bağımlılıkları

```bash
ansible-galaxy collection install kubernetes.core
```

## 4) Deploy

```bash
ansible-playbook -i ansible/inventory/hosts.ini ansible/deploy.yml
```

## 5) Oyun akışını test et

Gateway URL:

```bash
export GW_URL=$(minikube service gateway -n devops-demo --url)
```

Oyuncu event gönder:

```bash
curl -X POST "$GW_URL/play" -H "Content-Type: application/json" -d '{"player":"arda","action":"kill_monster"}'
curl -X POST "$GW_URL/play" -H "Content-Type: application/json" -d '{"player":"arda","action":"find_treasure"}'
curl -X POST "$GW_URL/play" -H "Content-Type: application/json" -d '{"player":"zeynep","action":"open_chest"}'
```

Skorları al:

```bash
curl "$GW_URL/score/arda"
curl "$GW_URL/leaderboard"
```

## Versiyon Güncelleme (Ansible ile)

`ansible/group_vars/all/versions.yml` içinde tag değiştir:

```yaml
gateway_image_tag: v0.2.0
processor_image_tag: v0.2.0
```

Sonra yeni imajları build edip tekrar deploy et:

```bash
ansible-playbook -i ansible/inventory/hosts.ini ansible/deploy.yml
```

## Temizlik

```bash
ansible-playbook -i ansible/inventory/hosts.ini ansible/destroy.yml
```
